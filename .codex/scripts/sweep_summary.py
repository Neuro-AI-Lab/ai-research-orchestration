#!/usr/bin/env python3
"""Fan-in a sweep's sub-runs into a markdown comparison table.

Usage: python3 .codex/scripts/sweep_summary.py experiments/codex/EXP-NNN

Reads experiments/codex/EXP-NNN/runs/*/status.json (written by run_with_status.sh) and, when present,
runs/*/metrics.json (flat {"metric": number} written by the evaluation step). Prints a markdown
table sorted by run tag: | run | state | exit | <metric columns...> |. Failed runs are kept in
the table — dropping them silently would misrepresent the sweep.
"""
import json
import os
import sys


def load(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 64
    sweep_dir = sys.argv[1].rstrip('/')
    runs_dir = os.path.join(sweep_dir, 'runs')
    if not os.path.isdir(runs_dir):
        print(f"sweep_summary: no runs/ directory under {sweep_dir}", file=sys.stderr)
        return 66

    rows = []
    metric_keys = []
    for tag in sorted(os.listdir(runs_dir)):
        run_dir = os.path.join(runs_dir, tag)
        if not os.path.isdir(run_dir):
            continue
        status = load(os.path.join(run_dir, 'status.json')) or {}
        metrics = load(os.path.join(run_dir, 'metrics.json')) or {}
        for key in metrics:
            if key not in metric_keys:
                metric_keys.append(key)
        rows.append((tag, status.get('state', 'unknown'),
                     status.get('exit_code'), metrics))

    if not rows:
        print(f"sweep_summary: no sub-runs found in {runs_dir}", file=sys.stderr)
        return 66

    header = ['run', 'state', 'exit'] + metric_keys
    print('| ' + ' | '.join(header) + ' |')
    print('|' + '|'.join([':--'] * len(header)) + '|')
    for tag, state, exit_code, metrics in rows:
        cells = [tag, state, 'null' if exit_code is None else str(exit_code)]
        cells += [str(metrics.get(k, '—')) for k in metric_keys]
        print('| ' + ' | '.join(cells) + ' |')

    incomplete = [t for t, s, _, _ in rows if s not in ('completed', 'failed')]
    if incomplete:
        print(f"\nWARNING: {len(incomplete)} sub-run(s) not finished yet: "
              + ', '.join(incomplete), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
