#!/usr/bin/env python3
"""Stop hook: ensure session-close recording happened before the main agent stops.

Two-layer continuity contract:
  - agent layer:  .claude/state/handoff.json  (structured; consumed by the SessionStart brief)
  - human layer:  STATE / doc entries in the root .md docs (readable monitoring)

If any Claude research doc or experiments/runs/ status changed after handoff.json was last updated, the first
stop attempt is blocked with instructions to update the hand-off (and a STATE entry when research
state changed). `stop_hook_active` guards against infinite loops: the retry is always allowed.
Output protocol: JSON {"decision":"block","reason":...} on stdout blocks; exit 0 silently allows.
"""
import json
import os
import sys

WATCH = ['report/discussion.md', 'report/issue.md', 'report/result.md', 'report/version.md']


def newest_mtime(root):
    newest = 0.0
    for name in WATCH:
        path = os.path.join(root, name)
        if os.path.isfile(path):
            newest = max(newest, os.path.getmtime(path))
    exp = os.path.join(root, 'experiments', 'claude')
    if os.path.isdir(exp):
        for sub in os.listdir(exp):
            spath = os.path.join(exp, sub, 'status.json')
            if os.path.isfile(spath):
                newest = max(newest, os.path.getmtime(spath))
    return newest


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if payload.get('stop_hook_active'):
        return 0  # second pass — never loop

    root = os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd()
    handoff = os.path.join(root, '.claude', 'state', 'handoff.json')
    if not os.path.isfile(handoff):
        return 0  # continuity is optional until `./orchestrate init` creates local state
    handoff_mtime = os.path.getmtime(handoff)

    if newest_mtime(root) <= handoff_mtime:
        return 0  # hand-off is current

    print(json.dumps({
        'decision': 'block',
        'reason': (
            'Session-close recording is stale: Claude research docs or experiment status changed after '
            '.claude/state/handoff.json was last written. Before stopping: '
            '(1) update .claude/state/handoff.json — fields: updated_at (ISO date), summary '
            '(1-2 sentences), open_items[], next_actions[], in_flight_runs[] (EXP-IDs still '
            'running), doc_pointers{} (latest STATE/EXP/REV ids); '
            '(2) if research state changed this session, ensure a STATE-YYYY-MM-DD entry exists '
            'in report/discussion.md (the active root/dedicated orchestrator owns coordination state); '
            '(3) then stop. Keep the hand-off dense — the next session reads it cold.'
        ),
    }))
    return 0


if __name__ == '__main__':
    sys.exit(main())
