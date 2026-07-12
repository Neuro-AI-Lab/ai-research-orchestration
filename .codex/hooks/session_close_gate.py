#!/usr/bin/env python3
"""Stop hook: ensure session-close recording happened before the main agent stops.

Two-layer continuity contract:
  - agent layer:  .codex/state/handoff.json  (structured; consumed by the SessionStart brief)
  - human layer:  STATE / doc entries in .codex/research/ (readable monitoring)

If any Codex research doc or experiments/codex status changed after handoff.json was last updated, the first
stop attempt is blocked with instructions to update the hand-off (and a STATE entry when research
state changed). `stop_hook_active` guards against infinite loops: the retry is always allowed.
Output protocol: JSON {"decision":"block","reason":...} on stdout blocks; exit 0 silently allows.
"""
import json
import os
import sys

WATCH = [
    '.codex/research/discussion.md',
    '.codex/research/error.md',
    '.codex/research/result.md',
    '.codex/research/version.md',
]


def newest_mtime(root):
    newest = 0.0
    for name in WATCH:
        path = os.path.join(root, name)
        if os.path.isfile(path):
            newest = max(newest, os.path.getmtime(path))
    exp = os.path.join(root, 'experiments', 'codex')
    if os.path.isdir(exp):
        for sub in os.listdir(exp):
            spath = os.path.join(exp, sub, 'status.json')
            if os.path.isfile(spath):
                newest = max(newest, os.path.getmtime(spath))
    return newest


def record_completed_stop(payload, root):
    """Record completion only after this gate knows no concurrent continuation is required."""
    if not os.environ.get('ORCHESTRATION_RUN_ID'):
        return
    try:
        sys.path.insert(0, os.path.join(root, '.codex', 'scripts'))
        from orchestration_audit import append_event, digest_text, purge_pending, safe_token
        append_event('session_stopped', {
            'session_id': safe_token(payload.get('session_id')),
            'turn_id': safe_token(payload.get('turn_id')),
            'result_sha256': digest_text(payload.get('last_assistant_message') or ''),
            'stop_hook_active': bool(payload.get('stop_hook_active')),
            'retained_content': False,
            'runtime_source': 'native_stop_gate',
        })
        purge_pending()
    except Exception:
        # The run remains visibly incomplete. Do not turn an audit-write failure into an infinite
        # Stop continuation loop.
        return


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    root = os.environ.get('CODEX_PROJECT_DIR') or os.getcwd()
    if payload.get('stop_hook_active'):
        record_completed_stop(payload, root)
        return 0  # second pass — never loop

    handoff = os.path.join(root, '.codex', 'state', 'handoff.json')
    if not os.path.isfile(handoff):
        record_completed_stop(payload, root)
        return 0  # continuity is optional until `./orchestrate init` creates local state
    handoff_mtime = os.path.getmtime(handoff)

    if newest_mtime(root) <= handoff_mtime:
        record_completed_stop(payload, root)
        return 0  # hand-off is current

    print(json.dumps({
        'decision': 'block',
        'reason': (
            'Session-close recording is stale: Codex research state changed after '
            '.codex/state/handoff.json was last written. Before stopping: '
            '(1) update .codex/state/handoff.json — fields: updated_at (ISO date), summary '
            '(1-2 sentences), open_items[], next_actions[], in_flight_runs[] (EXP-IDs still '
            'running), doc_pointers{} (latest STATE/EXP/REV ids); '
            '(2) if research state changed this session, ensure a STATE-YYYY-MM-DD entry exists '
            'in .codex/research/discussion.md; '
            '(3) then stop. Keep the hand-off dense — the next session reads it cold.'
        ),
    }))
    return 0


if __name__ == '__main__':
    sys.exit(main())
