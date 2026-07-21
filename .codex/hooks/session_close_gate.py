#!/usr/bin/env python3
"""Stop hook: record turn completion without blocking ordinary multi-turn use.

Codex emits Stop at a turn boundary, not only when a long-lived user session is permanently closed.
Therefore stale semantic handoff data is recorded as audit metadata but never returns a blocking
decision. SessionStart reconstructs safety-critical context from report/ and experiments/runs/ even
when `.codex/state/handoff.json` was not refreshed on the preceding turn.
"""
import json
import os
import sys


WATCH = [
    'plan/PRD.md',
    'plan/CHECKLIST.md',
    'report/discussion.md',
    'report/issue.md',
    'report/result.md',
    'report/version.md',
]


def newest_mtime(root):
    newest = 0.0
    for name in WATCH:
        path = os.path.join(root, name)
        if os.path.isfile(path):
            newest = max(newest, os.path.getmtime(path))
    exp = os.path.join(root, 'experiments', 'runs')
    if os.path.isdir(exp):
        for base, _dirs, files in os.walk(exp):
            if 'status.json' in files:
                newest = max(newest, os.path.getmtime(os.path.join(base, 'status.json')))
    return newest


def handoff_is_current(root):
    handoff = os.path.join(root, '.codex', 'state', 'handoff.json')
    if not os.path.isfile(handoff):
        return False
    return newest_mtime(root) <= os.path.getmtime(handoff)


def record_completed_stop(payload, root, continuity_current):
    """Best-effort metadata recording; continuity freshness never blocks the user."""
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
            'continuity_current': bool(continuity_current),
            'retained_content': False,
            'runtime_source': 'native_nonblocking_stop_hook',
        })
        purge_pending()
    except Exception:
        return


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    root = os.environ.get('CODEX_PROJECT_DIR') or os.getcwd()
    record_completed_stop(payload, root, handoff_is_current(root))
    return 0


if __name__ == '__main__':
    sys.exit(main())
