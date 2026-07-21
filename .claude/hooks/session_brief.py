#!/usr/bin/env python3
"""SessionStart hook: inject a situational brief so agents resume where the last session stopped.

Stdout from this hook is added to the session context. It surfaces, mechanically (no LLM):
  - the structured hand-off from the previous session (.claude/state/handoff.json)
  - open critical BUGs (.claude/research/error.md) and open blocking REVs (.claude/research/discussion.md)
  - the most recent STATE entry header (.claude/research/discussion.md)
  - experiment runs still marked running (experiments/claude/*/status.json), with pid liveness,
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


def field_passed(block, field):
    found = re.findall(
        r'(?mi)^\*{0,2}' + re.escape(field) + r':\*{0,2}\s*([^\n]+)', block
    )
    return bool(found and found[-1].strip().lower() in {'pass', 'passed', 'approved', 'clear'})


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
        def clip(text, limit):
            text = str(text)
            return text if len(text) <= limit else text[:limit].rstrip() + ' … [read handoff.json for the rest]'

        lines.append(f"- Last hand-off ({handoff.get('updated_at', '?')}): "
                     f"{clip(handoff.get('summary', '(no summary)'), 600)}")
        for item in handoff.get('next_actions', [])[:6]:
            lines.append(f'  - next: {clip(item, 300)}')
        for item in handoff.get('open_items', [])[:6]:
            lines.append(f'  - open: {clip(item, 300)}')
    except (OSError, ValueError):
        lines.append('- No hand-off file yet (.claude/state/handoff.json) — first session or '
                     'previous session ended without closing properly.')

    error, discussion = read(root, '.claude/research/error.md'), read(root, '.claude/research/discussion.md')
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

    discussion_blocks = entry_blocks(discussion)
    positive = {
        'critic REV': any(re.match(r'## \[REV-\d+\]', block) and field_passed(block, 'Gate')
                          for block in discussion_blocks),
        'QA': any(re.match(r'## \[QA-\d+\]', block) and field_passed(block, 'Gate')
                  for block in discussion_blocks),
        'DATASET leakage audit': any(
            re.match(r'## \[DATASET-\d+\]', block) and field_passed(block, 'Leakage audit')
            for block in discussion_blocks
        ),
    }
    pending = [name for name, passed in positive.items() if not passed]
    if pending:
        lines.append('- GATE: experiments still need positive attestation(s): ' + ', '.join(pending))
    elif not bugs and not revs:
        lines.append('- GATE: positive critic, QA, and DATASET attestations are present')

    states = re.findall(r'(?m)^## \[(STATE-[0-9-]+)\]', discussion)
    if states:
        lines.append(f'- Last STATE entry: {states[-1]} (read .claude/research/discussion.md for detail)')

    exp_dir = os.path.join(root, 'experiments', 'claude')
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
