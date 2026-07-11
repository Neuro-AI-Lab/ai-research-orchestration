#!/usr/bin/env python3
"""PreToolUse hook: mechanical enforcement of the experiment gates.

Blocks Bash commands that launch experiments (run.sh / evaluate.sh / python models/*.py)
while any mandatory gate is unmet:
  - open critical BUG in error.md          (QA gate)
  - open blocking REV in discussion.md     (critic gate)
  - no DATASET entry in discussion.md      (data gate / bootstrap rule)

Documented bypass (mirrors CLAUDE.md "When to break the rules"): write an ADR in
discussion.md naming the skipped rule, reason, and rollback plan, then prefix the
command with GATE_OVERRIDE=ADR-NNN. The hook verifies the ADR actually exists.

Exit 0 = allow. Exit 2 = block; stderr is returned to the agent.
"""
import json
import os
import re
import sys

# Match run.sh / evaluate.sh / python models/*.py only in COMMAND-WORD position within a
# shell command *segment* — never as a substring anywhere in the text. A segment is what
# runs between shell control operators (;, &, &&, |, ||, (, )) or at the very start of the
# command. Within a segment, the command word may be preceded by env-var assignments
# (NAME=value ...) and/or an interpreter keyword (bash/sh/zsh/source/./setsid/nohup/exec).
# This is why read-only mentions pass through — `cat run.sh`, `grep run.sh README.md`,
# `echo "run.sh"`, `wc -l setup.sh evaluate.sh` (a *.sh filename tail is not a "sh"
# interpreter word) — while real launches in any position (leading, after ;/&&/|, behind an
# env-assignment prefix such as GATE_OVERRIDE=..., or as an interpreter's script argument
# without a `bash -n` syntax-check flag in between) still match.
#
# BUG-004: a raw character-class split on `;&|()\n` is quote/heredoc-unaware -- a control
# character sitting *inside* a quoted string (`grep -E "run.sh|evaluate.sh"`, `echo
# "(run.sh)"`) or a `\n` inside a heredoc body (`cat <<EOF` / `run.sh` / `EOF`) still
# produced a segment boundary, carving out a bare `run.sh`/`evaluate.sh` segment that then
# matched _SCRIPT_LAUNCH even though the text is data, not shell syntax. Fixed below by
# `_split_segments` (quote-tracking scan) and `_mask_heredocs` (blanks heredoc body lines
# before splitting). `_SEGMENT_SPLIT` itself is kept only as the legacy fallback splitter --
# see `is_experiment_launch`.
_SEGMENT_SPLIT = re.compile(r'&&|\|\||[;&|()\n]')
_ENV_ASSIGN = r'(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*'
_INTERPRETER = r'(?:(?:bash|sh|zsh|setsid|nohup|exec|source)\s+|\.\s+)?'
_PATH_PREFIX = r'(?:\./)?(?:[\w.-]+/)*'
_SCRIPT_LAUNCH = re.compile(r'^' + _ENV_ASSIGN + _INTERPRETER + _PATH_PREFIX + r'(run|evaluate)\.sh\b')
_PYTHON_LAUNCH = re.compile(r'^' + _ENV_ASSIGN + r'python[0-9.]*\s+\S*models/\S+\.py')

# Heredoc start marker: `<<WORD`, `<<-WORD` (indented terminator), `<<'WORD'`/`<<"WORD"`
# (quoted, suppresses expansion) or `<<\WORD` (backslash-escaped, same effect). The captured
# group is the literal delimiter word used to find the end of the body below.
_HEREDOC_START = re.compile(r'<<-?\s*(?:["\'\\])?([A-Za-z_][A-Za-z0-9_]*)')

# A single leading env-var assignment, as consumed one at a time from the front of a
# segment -- mirrors the repeated group inside `_ENV_ASSIGN` above but capturing the
# name/value pair so BUG-006's override check can walk the same prefix the launch
# regexes already matched against, instead of re-scanning the whole command string.
_ENV_ASSIGN_ITEM = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)=(\S*)\s+')


def _mask_heredocs(cmd):
    """Blank out heredoc body lines so they are never mistaken for shell segments.

    A heredoc (`cat <<EOF` ... body ... `EOF`) redirects literal text -- not shell syntax --
    into the preceding command's stdin. Body lines are replaced with empty strings (not
    removed) so line/segment structure outside the heredoc is unaffected; only a run of `\\n`
    splits results, which the scanner below treats as empty segments and skips.

    Known, accepted limitation: this intentionally does not attempt to detect a launch
    smuggled *through* a heredoc fed to a shell interpreter (e.g. `bash <<EOF` / `./run.sh` /
    `EOF`, or process substitution, or `eval "$(...)"`). Reasoning that deep about shell
    semantics is out of scope for a command-word-position heuristic gate (see the hook's
    module docstring); it was never reliably covered before this fix either, and closing it
    would require a real shell parser, not a hardening pass on BUG-004.
    """
    lines = cmd.split('\n')
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        out.append(line)
        match = _HEREDOC_START.search(line)
        i += 1
        if not match:
            continue
        delim = match.group(1)
        while i < n and lines[i].strip() != delim:
            out.append('')
            i += 1
        if i < n:
            out.append('')  # blank the delimiter line itself too
            i += 1
    return '\n'.join(out)


def _split_segments(cmd):
    """Split `cmd` into shell command segments, tracking quote state.

    Mirrors `_SEGMENT_SPLIT` (splits on unescaped, unquoted &&, ||, ;, &, |, (, ), \\n) but
    a control character inside a single- or double-quoted string, or backslash-escaped
    outside quotes, is treated as literal text rather than a boundary -- this is what
    `grep -E "run.sh|evaluate.sh"` and `echo "(run.sh)"` need to stay a single segment.
    Pure linear character scan over a bounded string with no external parser call (no
    shlex): it cannot raise. `is_experiment_launch` still wraps the call in a `try/except`
    as cheap defense-in-depth, per the constraint that this hook must never crash a
    PreToolUse call.
    """
    segments = []
    buf = []
    in_single = False
    in_double = False
    i = 0
    n = len(cmd)
    while i < n:
        c = cmd[i]
        if in_single:
            buf.append(c)
            if c == "'":
                in_single = False
            i += 1
            continue
        if in_double:
            if c == '\\' and i + 1 < n:
                buf.append(c)
                buf.append(cmd[i + 1])
                i += 2
                continue
            buf.append(c)
            if c == '"':
                in_double = False
            i += 1
            continue
        # Not inside any quote.
        if c == "'":
            in_single = True
            buf.append(c)
            i += 1
            continue
        if c == '"':
            in_double = True
            buf.append(c)
            i += 1
            continue
        if c == '\\' and i + 1 < n:
            buf.append(c)
            buf.append(cmd[i + 1])
            i += 2
            continue
        if c == '&' and cmd[i:i + 2] == '&&':
            segments.append(''.join(buf))
            buf = []
            i += 2
            continue
        if c == '|' and cmd[i:i + 2] == '||':
            segments.append(''.join(buf))
            buf = []
            i += 2
            continue
        if c in ';&|()\n':
            segments.append(''.join(buf))
            buf = []
            i += 1
            continue
        buf.append(c)
        i += 1
    segments.append(''.join(buf))
    return segments


def find_launch_segments(cmd):
    """Return the stripped command segments of `cmd` that are actual script launches.

    Shared by `is_experiment_launch` and the BUG-006 override check so both look at
    exactly the same set of segments -- launch detection and override matching must
    never disagree about which piece of the command is "the launch".
    """
    try:
        segments = _split_segments(_mask_heredocs(cmd))
    except Exception:
        # Never let a hook crash break a Bash call. Fall back to the legacy quote-unaware
        # splitter (the pre-BUG-004-fix behavior): conservative and prone to false-positive
        # blocks on quoted/heredoc mentions, but that is strictly safer for a security gate
        # than either crashing the hook or failing open (returning False unconditionally).
        segments = _SEGMENT_SPLIT.split(cmd)
    launches = []
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        if _SCRIPT_LAUNCH.match(segment) or _PYTHON_LAUNCH.match(segment):
            launches.append(segment)
    return launches


def is_experiment_launch(cmd):
    """Return True iff `cmd` contains a run.sh/evaluate.sh/python-models launch in command-word position."""
    return bool(find_launch_segments(cmd))


def leading_override(segment):
    """Return the ADR id (e.g. 'ADR-002') if GATE_OVERRIDE=ADR-NNN is a leading
    env-assignment on `segment`, else None.

    BUG-006: the override token must be tied to the *same launch segment*, in the same
    leading-assignment position `_SCRIPT_LAUNCH`/`_PYTHON_LAUNCH` already require --
    never merely present somewhere else in the raw command (a comment, an echo, a
    different segment). Walks the same repeated `NAME=value ` prefix `_ENV_ASSIGN`
    matches, so `FOO=1 GATE_OVERRIDE=ADR-002 ./run.sh train` still finds it after `FOO=1`.
    """
    rest = segment
    while True:
        match = _ENV_ASSIGN_ITEM.match(rest)
        if not match:
            return None
        name, value = match.group(1), match.group(2)
        if name == 'GATE_OVERRIDE':
            return value if re.fullmatch(r'ADR-\d+', value) else None
        rest = rest[match.end():]


def entry_blocks(text):
    parts = re.split(r'(?m)^## \[', text)
    return ['## [' + p for p in parts[1:]]


def entry_id(block):
    end = block.find(']')
    return block[4:end] if end > 4 else 'UNKNOWN'


def last_status(block):
    found = re.findall(r'(?mi)^\*\*Status:\*\*\s*(\w+)', block)
    return found[-1].lower() if found else None


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if payload.get('tool_name') != 'Bash':
        return 0
    cmd = (payload.get('tool_input') or {}).get('command', '') or ''
    launch_segments = find_launch_segments(cmd)
    if not launch_segments:
        return 0

    root = os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd()

    def read(name):
        try:
            with open(os.path.join(root, name), encoding='utf-8') as fh:
                return fh.read()
        except OSError:
            return ''

    discussion = read('discussion.md')
    error = read('error.md')

    # BUG-006: only accept an override cited as a leading env-assignment on the
    # segment it is meant to protect -- never merely mentioned elsewhere in the raw
    # command (comment, echo, unrelated segment).
    #
    # BUG-007: an override on *one* launch segment must not authorize a *different*
    # launch segment that carries none of its own. Each launch segment is checked for
    # its own leading override; the whole command is only bypassed if every launch
    # segment individually cites a valid one. A cited-but-nonexistent ADR is rejected
    # immediately regardless of the other segments' state (fail closed, existing
    # message). If any segment has no override at all, the override path does not
    # apply and the command falls through to the normal gate checks below.
    segment_overrides = [(segment, leading_override(segment)) for segment in launch_segments]
    for segment, override_adr in segment_overrides:
        if override_adr and not re.search(r'## \[' + re.escape(override_adr) + r'\]', discussion):
            print(
                f"GATE: override cited {override_adr}, but no such ADR exists in "
                "discussion.md. Write the ADR (rule skipped, reason, rollback plan) first.",
                file=sys.stderr,
            )
            return 2
    if all(override_adr for _segment, override_adr in segment_overrides):
        return 0

    problems = []
    for block in entry_blocks(error):
        if (block.startswith('## [BUG-')
                and re.search(r'(?mi)^\*\*Severity:\*\*\s*critical', block)
                and last_status(block) == 'open'):
            problems.append(f'open critical {entry_id(block)} in error.md')
    for block in entry_blocks(discussion):
        if (block.startswith('## [REV-')
                and re.search(r'(?mi)^\*\*Severity:\*\*\s*blocking', block)
                and last_status(block) == 'open'):
            problems.append(f'open blocking {entry_id(block)} in discussion.md')
    if not re.search(r'## \[DATASET-\d+\]', discussion):
        problems.append('no DATASET entry in discussion.md (split undocumented / bootstrap incomplete)')

    if problems:
        print(
            'GATE BLOCKED - experiment launch stopped by the mechanical gate '
            '(.claude/hooks/experiment_gate.py):\n  - ' + '\n  - '.join(problems) +
            '\nResolve the items above, or record a bypass ADR in discussion.md '
            '(rule skipped, reason, rollback plan) and re-run the command with '
            'GATE_OVERRIDE=ADR-NNN prefixed.',
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
