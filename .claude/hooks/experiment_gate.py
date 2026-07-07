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

EXP_LAUNCH = re.compile(
    r'(^|[\s;&|(])(bash\s+|sh\s+|\./)?(run|evaluate)\.sh\b'
    r'|python[0-9.]*\s+\S*models/\S+\.py'
)


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
    if not EXP_LAUNCH.search(cmd):
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

    override = re.search(r'GATE_OVERRIDE=(ADR-\d+)', cmd)
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
