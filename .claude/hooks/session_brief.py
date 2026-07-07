#!/usr/bin/env python3
"""SessionStart hook: inject a situational brief so agents resume where the last session stopped.

Stdout from this hook is added to the session context. It surfaces, mechanically (no LLM):
  - the structured hand-off from the previous session (.claude/state/handoff.json)
  - open critical BUGs (error.md) and open blocking REVs (discussion.md)
  - the most recent STATE entry header (discussion.md)
  - experiment runs still marked running (experiments/*/status.json), with pid liveness,
    so orphaned long runs are adopted instead of forgotten.
"""
import json
import os
import re
import sys


def read(root, name):
    try:
        with open(os.path.join(root, name), encoding='utf-8') as fh:
            return fh.read()
    except OSError:
        return ''


def entry_blocks(text):
    return ['## [' + p for p in re.split(r'(?m)^## \[', text)[1:]]


def last_status(block):
    found = re.findall(r'(?mi)^\*\*Status:\*\*\s*(\w+)', block)
    return found[-1].lower() if found else None


def entry_id(block):
    end = block.find(']')
    return block[4:end] if end > 4 else 'UNKNOWN'


def pid_alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError, TypeError):
        return False


def main():
    root = os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd()
    lines = ['[session-brief] Automatic continuity brief (SessionStart hook):']

    handoff_path = os.path.join(root, '.claude', 'state', 'handoff.json')
    try:
        with open(handoff_path, encoding='utf-8') as fh:
            handoff = json.load(fh)
        lines.append(f"- Last hand-off ({handoff.get('updated_at', '?')}): "
                     f"{handoff.get('summary', '(no summary)')}")
        for item in handoff.get('next_actions', [])[:6]:
            lines.append(f'  - next: {item}')
        for item in handoff.get('open_items', [])[:6]:
            lines.append(f'  - open: {item}')
    except (OSError, ValueError):
        lines.append('- No hand-off file yet (.claude/state/handoff.json) — first session or '
                     'previous session ended without closing properly.')

    error, discussion = read(root, 'error.md'), read(root, 'discussion.md')
    bugs = [entry_id(b) for b in entry_blocks(error)
            if b.startswith('## [BUG-')
            and re.search(r'(?mi)^\*\*Severity:\*\*\s*critical', b)
            and last_status(b) == 'open']
    revs = [entry_id(b) for b in entry_blocks(discussion)
            if b.startswith('## [REV-')
            and re.search(r'(?mi)^\*\*Severity:\*\*\s*blocking', b)
            and last_status(b) == 'open']
    if bugs:
        lines.append(f"- GATE: open critical BUGs block all experiments: {', '.join(bugs)}")
    if revs:
        lines.append(f"- GATE: open blocking REVs: {', '.join(revs)}")

    states = re.findall(r'(?m)^## \[(STATE-[0-9-]+)\]', discussion)
    if states:
        lines.append(f'- Last STATE entry: {states[-1]} (read discussion.md for detail)')

    exp_dir = os.path.join(root, 'experiments')
    if os.path.isdir(exp_dir):
        for sub in sorted(os.listdir(exp_dir)):
            spath = os.path.join(exp_dir, sub, 'status.json')
            if not os.path.isfile(spath):
                continue
            try:
                with open(spath, encoding='utf-8') as fh:
                    st = json.load(fh)
            except (OSError, ValueError):
                continue
            if st.get('state') == 'running':
                alive = pid_alive(st.get('pid'))
                lines.append(
                    f"- RUN {st.get('exp_id', sub)}: status=running, pid "
                    f"{'ALIVE — monitor it' if alive else 'DEAD — ORPHANED, adopt it (tracker protocol)'}"
                    f" (log: {st.get('log', '?')})")

    if len(lines) == 1:
        lines.append('- Clean slate: no hand-off, no open gates, no running experiments.')
    print('\n'.join(lines))
    return 0


if __name__ == '__main__':
    sys.exit(main())
