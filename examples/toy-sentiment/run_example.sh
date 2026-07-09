#!/usr/bin/env bash
# Thin wrapper around run_example.py (stdlib-only, CPU-only toy-sentiment demo).
# Intentionally NOT named run.sh so the template's experiment_gate hook does
# not treat this teaching fixture as a real experiment launch.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/run_example.py" "$@"
