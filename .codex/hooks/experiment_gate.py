#!/usr/bin/env python3
"""PreToolUse hook: mechanical enforcement of the experiment gates.

Blocks Bash commands that launch experiments (run.sh / evaluate.sh / python models/*.py)
while any mandatory gate is unmet:
  - open critical BUG in .codex/research/error.md
  - open blocking REV in .codex/research/discussion.md
  - no passed critic REV in the Codex discussion
  - no passed QA entry in the Codex discussion
  - no leakage-audited DATASET entry        (positive data attestation)

Documented bypass (mirrors .codex/ORCHESTRATION.md "When to break the rules"): write an ADR in
.codex/research/discussion.md naming the skipped rule, reason, and rollback plan, then prefix the
command with GATE_OVERRIDE=ADR-NNN. The hook verifies the ADR exists and carries the mandatory
Context, Decision, Consequences, and Rollback fields.

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
# Quote-aware segmentation and heredoc masking prevent data strings from being treated as
# executable shell segments. The regular-expression splitter is only a fail-closed fallback.
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
_SHELL_STDIN = re.compile(
    r'^' + _ENV_ASSIGN + r'(?:(?:setsid|nohup|exec)\s+)*(?:bash|sh|zsh)\b'
)

# A single leading env-var assignment, as consumed one at a time from the front of a
# segment -- mirrors the repeated group inside `_ENV_ASSIGN` above but capturing the
# name/value pair so the override check walks the same prefix as launch detection.
_ENV_ASSIGN_ITEM = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)=(\S*)\s+')


def _heredoc_shell_launches(cmd):
    """Return shell-interpreter heredoc headers whose bodies launch experiments.

    `cat <<EOF` bodies remain data and are ignored. A body fed to bash/sh/zsh is executable
    shell input, so launch-looking command words inside it must be gated. Returning the header
    preserves a leading GATE_OVERRIDE assignment on that exact interpreter segment.
    """
    lines = cmd.split('\n')
    launches = []
    i = 0
    while i < len(lines):
        header = lines[i]
        marker = _HEREDOC_START.search(header)
        i += 1
        if not marker:
            continue
        delim = marker.group(1)
        body = []
        while i < len(lines) and lines[i].strip() != delim:
            body.append(lines[i])
            i += 1
        if i < len(lines):
            i += 1
        header_segments = _split_segments(header[:marker.start()])
        header_segment = header_segments[-1].strip() if header_segments else ''
        if not _SHELL_STDIN.match(header_segment):
            continue
        for segment in _split_segments('\n'.join(body)):
            candidate = segment.strip()
            if _SCRIPT_LAUNCH.match(candidate) or _PYTHON_LAUNCH.match(candidate):
                launches.append(header_segment)
    return launches


def _mask_heredocs(cmd):
    """Blank out heredoc body lines so they are never mistaken for shell segments.

    A heredoc (`cat <<EOF` ... body ... `EOF`) redirects literal text -- not shell syntax --
    into the preceding command's stdin. Body lines are replaced with empty strings (not
    removed) so line/segment structure outside the heredoc is unaffected; only a run of `\\n`
    splits results, which the scanner below treats as empty segments and skips.

    Shell-interpreter heredocs are scanned separately by `_heredoc_shell_launches`; bodies fed
    to non-shell commands remain data. Process substitution and dynamic eval are outside this
    heuristic gate and must be controlled by the runtime sandbox and review policy.
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

    Launch detection and override matching consume this same segment set so they cannot
    disagree about which piece of the command is the launch.
    """
    try:
        segments = _split_segments(_mask_heredocs(cmd))
    except Exception:
        # Never let a hook crash break a Bash call. The conservative fallback can produce
        # false-positive blocks, which is safer here than failing open.
        segments = _SEGMENT_SPLIT.split(cmd)
    launches = _heredoc_shell_launches(cmd)
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

    The override must be a leading assignment on the same launch segment, never a token
    in a comment, an echo, or a different segment. Other leading assignments may precede it.
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
    found = re.findall(r'(?mi)^\*{0,2}Status:\*{0,2}\s*([\w-]+)', block)
    return found[-1].lower() if found else None


def field_value(block, field):
    found = re.findall(
        r'(?mi)^\*{0,2}' + re.escape(field) + r':\*{0,2}\s*([^\n]+)', block
    )
    return found[-1].strip().lower() if found else None


def field_passed(block, field):
    value = field_value(block, field) or ''
    return value in {'pass', 'passed', 'approved', 'clear'}


def record_audit_gate(payload, command, launch_segments, decision, reason_codes, override_ids=None):
    """Best-effort metadata-only audit; gate enforcement never depends on logging."""
    if not os.environ.get('ORCHESTRATION_RUN_ID'):
        return
    try:
        root = os.environ.get('CODEX_PROJECT_DIR') or os.getcwd()
        sys.path.insert(0, os.path.join(root, '.codex', 'scripts'))
        from orchestration_audit import append_event, digest_text, safe_token
        append_event('research_gate', {
            'session_id': safe_token(payload.get('session_id')),
            'turn_id': safe_token(payload.get('turn_id')),
            'tool_use_id': safe_token(payload.get('tool_use_id')),
            'decision': decision,
            'reason_codes': list(reason_codes),
            'override_ids': [safe_token(value) for value in (override_ids or [])],
            'launch_segment_count': len(launch_segments),
            'command_sha256': digest_text(command),
            'retained_content': False,
            'runtime_source': 'native_hook',
        })
    except Exception:
        # The mechanical safety decision below remains authoritative. A missing audit event is
        # visible later as absent evidence; it must never turn an allow into a crash or a block
        # into a bypass.
        return


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

    root = os.environ.get('CODEX_PROJECT_DIR') or os.getcwd()

    def read(name):
        try:
            with open(os.path.join(root, name), encoding='utf-8') as fh:
                return fh.read()
        except OSError:
            return ''

    discussion = read('.codex/research/discussion.md')
    error = read('.codex/research/error.md')

    # An override applies only to its own launch segment. Every launch segment must cite
    # a valid ADR for the whole command to bypass the normal gates; missing or incomplete
    # citations fail closed.
    segment_overrides = [(segment, leading_override(segment)) for segment in launch_segments]
    for segment, override_adr in segment_overrides:
        if not override_adr:
            continue
        adr_blocks = [
            block for block in entry_blocks(discussion)
            if re.match(r'## \[' + re.escape(override_adr) + r'\]', block)
        ]
        if not adr_blocks:
            record_audit_gate(
                payload, cmd, launch_segments, 'block', ['override_adr_missing'], [override_adr]
            )
            print(
                f"GATE: override cited {override_adr}, but no such ADR exists in "
                ".codex/research/discussion.md. Write the ADR first.",
                file=sys.stderr,
            )
            return 2
        required_adr_fields = ('Context', 'Decision', 'Consequences', 'Rollback')
        missing = [field for field in required_adr_fields if not field_value(adr_blocks[-1], field)]
        if missing:
            record_audit_gate(
                payload, cmd, launch_segments, 'block', ['override_adr_incomplete'], [override_adr]
            )
            print(
                f"GATE: override ADR {override_adr} is incomplete; add fields: " +
                ", ".join(missing) + ".",
                file=sys.stderr,
            )
            return 2
    if all(override_adr for _segment, override_adr in segment_overrides):
        record_audit_gate(
            payload, cmd, launch_segments, 'allow', ['adr_override'],
            [override_adr for _segment, override_adr in segment_overrides],
        )
        return 0

    problems = []
    for block in entry_blocks(error):
        if (re.match(r'## \[BUG-\d+\]', block)
                and re.search(r'(?mi)^\*{0,2}Severity:\*{0,2}\s*critical', block)
                and last_status(block) == 'open'):
            problems.append(f'open critical {entry_id(block)} in .codex/research/error.md')
    for block in entry_blocks(discussion):
        if (re.match(r'## \[REV-\d+\]', block)
                and re.search(r'(?mi)^\*{0,2}Severity:\*{0,2}\s*blocking', block)
                and last_status(block) == 'open'):
            problems.append(f'open blocking {entry_id(block)} in .codex/research/discussion.md')
    blocks = entry_blocks(discussion)
    dataset_blocks = [block for block in blocks if re.match(r'## \[DATASET-\d+\]', block)]
    critic_blocks = [block for block in blocks if re.match(r'## \[REV-\d+\]', block)]
    qa_blocks = [block for block in blocks if re.match(r'## \[QA-\d+\]', block)]
    if not any(field_passed(block, 'Leakage audit') for block in dataset_blocks):
        problems.append('no DATASET entry with **Leakage audit:** passed in Codex research state')
    if not any(field_passed(block, 'Gate') for block in critic_blocks):
        problems.append('no critic REV entry with **Gate:** passed in Codex research state')
    if not any(field_passed(block, 'Gate') for block in qa_blocks):
        problems.append('no QA entry with **Gate:** passed in Codex research state')

    if problems:
        reason_codes = []
        for problem in problems:
            if problem.startswith('open critical'):
                reason_codes.append('open_critical_bug')
            elif problem.startswith('open blocking'):
                reason_codes.append('open_blocking_review')
            elif problem.startswith('no DATASET'):
                reason_codes.append('missing_leakage_attestation')
            elif problem.startswith('no critic'):
                reason_codes.append('missing_critic_attestation')
            elif problem.startswith('no QA'):
                reason_codes.append('missing_qa_attestation')
        record_audit_gate(payload, cmd, launch_segments, 'block', reason_codes)
        print(
            'GATE BLOCKED - experiment launch stopped by the mechanical gate '
            '(.codex/hooks/experiment_gate.py):\n  - ' + '\n  - '.join(problems) +
            '\nResolve the items above, or record a bypass ADR in .codex/research/discussion.md '
            '(rule skipped, reason, rollback plan) and re-run the command with '
            'GATE_OVERRIDE=ADR-NNN prefixed.',
            file=sys.stderr,
        )
        return 2
    record_audit_gate(payload, cmd, launch_segments, 'allow', ['all_attestations_passed'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
