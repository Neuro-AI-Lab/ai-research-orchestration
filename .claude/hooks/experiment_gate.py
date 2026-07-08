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

# A command "segment" is the text at the very start of the command string, or the
# text immediately following a shell control operator (`;`, `&`, `|`) or a
# subshell-open `(`, with any whitespace right after the operator skipped. Launch
# detection below anchors to these exact offsets via re.match (not re.search), so a
# keyword like "sh" can never be matched as the trailing substring of an unrelated
# token such as "setup.sh " -- it must actually be the first word of a segment
# (BUG-001/BUG-002 root cause: the old regex used `\b`, which matches inside tokens
# too, and had no anchor at all on the python alternative).
_SEGMENT_OPS = re.compile(r'[;&|]|\(')

# Zero or more leading `NAME=value` shell assignments (e.g. `GATE_OVERRIDE=ADR-001`,
# `CUDA_VISIBLE_DEVICES=0`), captured as one block, so a launch prefixed by env
# assignments is still recognized as being in command position (fixes BUG-001: a
# leading `NAME=value ` no longer breaks the anchor and silently bypasses the gate).
_ENV_CHAIN = (
    r'((?:[A-Za-z_][A-Za-z0-9_]*='
    r'(?:"[^"]*"|\'[^\']*\'|\S*)\s+)*)'
)

# An optional single executor keyword immediately preceding the script/module, e.g.
# `bash run.sh`, `nohup ./run.sh`. Anchored via re.match at the exact segment offset,
# so (unlike the old `\b`-based version) it can never match the "sh" tail of an
# adjacent `*.sh` filename (e.g. `wc -l setup.sh evaluate.sh` no longer misreads the
# "sh " at the end of "setup.sh" as the `sh` interpreter being invoked).
_EXECUTOR = r'(?:(?:bash|sh|setsid|nohup|exec)\s+)?'

_SCRIPT_LAUNCH = re.compile(_ENV_CHAIN + _EXECUTOR + r'(?:\./)?(?:run|evaluate)\.sh\b')
# Same command-position anchor now applied to the python alternative (fixes BUG-002:
# previously unanchored, so it matched a `python models/*.py` substring anywhere in
# the command text, including inside quoted/read-only arguments to grep/echo/cat).
_PY_LAUNCH = re.compile(_ENV_CHAIN + _EXECUTOR + r'python[0-9.]*\s+\S*models/\S+\.py\b')

_OVERRIDE = re.compile(r'GATE_OVERRIDE=(ADR-\d+)')


def _segment_starts(cmd):
    """Yield offsets in cmd where a new shell command segment begins."""
    yield 0
    for m in _SEGMENT_OPS.finditer(cmd):
        pos = m.end()
        while pos < len(cmd) and cmd[pos].isspace():
            pos += 1
        yield pos


def find_launch_env_chain(cmd):
    """Return the leading env-assignment text of the first experiment-launch segment
    in cmd, or None if cmd contains no experiment launch in command position.

    A match requires the launch (run.sh/evaluate.sh/python models/*.py, optionally
    behind env assignments and/or a single executor keyword) to sit at the exact
    start of a command segment -- read-only mentions inside other arguments (e.g.
    `grep 'python models/train.py' README.md`, `cat run.sh`, `wc -l setup.sh
    evaluate.sh`) never match. The returned text is also where a GATE_OVERRIDE=ADR-NNN
    prefix is looked for, so an override embedded elsewhere in the command (e.g. inside
    an unrelated quoted string) cannot be mistaken for a real override.
    """
    for start in _segment_starts(cmd):
        m = _SCRIPT_LAUNCH.match(cmd, start) or _PY_LAUNCH.match(cmd, start)
        if m:
            return m.group(1)
    return None


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
    env_chain = find_launch_env_chain(cmd)
    if env_chain is None:
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

    override = _OVERRIDE.search(env_chain)
    if override:
        if re.search(r'## \[' + re.escape(override.group(1)) + r'\]', discussion):
            return 0
        print(
            f"GATE: override cited {override.group(1)}, but no such ADR exists in "
            "discussion.md. Write the ADR (rule skipped, reason, rollback plan) first.",
            file=sys.stderr,
        )
        return 2

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
