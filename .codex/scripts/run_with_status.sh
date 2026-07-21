#!/usr/bin/env bash
# Launch an experiment command with status tracking and a heartbeat.
#
# Usage:  .codex/scripts/run_with_status.sh EXP-NNN [--tag RUN-TAG] -- <command...>
# Writes: ${EXPERIMENTS_DIR:-experiments/runs}/EXP-NNN/status.json  (state machine:
#         launched -> running -> completed|failed, with pid/heartbeat/exit_code)
#         ${EXPERIMENTS_DIR:-experiments/runs}/EXP-NNN/run.log      (all output, appended)
#
# Invoke inside a backgrounded Bash call. The command itself runs under setsid,
# so it survives if the launching session dies; in that case status.json is left
# in state=running with a dead wrapper pid — the session-start adoption procedure
# in the experiment-tracker spec detects and handles exactly that.
set -u

EXP_ID="${1:?usage: run_with_status.sh EXP-NNN [--tag RUN-TAG] -- <command...>}"
shift
case "$EXP_ID" in
  EXP-*) ;;
  *) echo "run_with_status.sh: experiment id must be EXP-NNN" >&2; exit 64 ;;
esac
case "${EXP_ID#EXP-}" in
  *[!0-9]*|'') echo "run_with_status.sh: experiment id must be EXP-NNN" >&2; exit 64 ;;
esac
RUN_TAG=""
if [ "${1:-}" = "--tag" ]; then
  RUN_TAG="${2:?run_with_status.sh: --tag requires a value}"
  case "$RUN_TAG" in
    *[!A-Za-z0-9_.-]*|'') echo "run_with_status.sh: invalid run tag" >&2; exit 64 ;;
  esac
  shift 2
fi
[ "${1:-}" = "--" ] && shift
[ "$#" -ge 1 ] || { echo "run_with_status.sh: no command given" >&2; exit 64; }

EXP_DIR="${EXPERIMENTS_DIR:-experiments/runs}/$EXP_ID"
if [ -n "$RUN_TAG" ]; then
  RUN_DIR="$EXP_DIR/runs/$RUN_TAG"
  RUN_TAG_JSON="\"$RUN_TAG\""
else
  RUN_DIR="$EXP_DIR"
  RUN_TAG_JSON="null"
fi
mkdir -p "$RUN_DIR"
STATUS="$RUN_DIR/status.json"
LOG="$RUN_DIR/run.log"
STARTED="$(date -Is)"
CMD_JSON=$(python3 -c 'import json,sys; print(json.dumps(" ".join(sys.argv[1:])))' "$@")
LOG_JSON=$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$LOG")

write_status() { # $1=state $2=exit_code(or null)
  printf '{"exp_id":"%s","run_tag":%s,"state":"%s","pid":%d,"started_at":"%s","last_heartbeat":"%s","exit_code":%s,"log":%s,"cmd":%s}\n' \
    "$EXP_ID" "$RUN_TAG_JSON" "$1" "$$" "$STARTED" "$(date -Is)" "${2:-null}" "$LOG_JSON" "$CMD_JSON" > "$STATUS"
}

write_status launched null
( while kill -0 "$$" 2>/dev/null; do write_status running null; sleep 30; done ) &
HEARTBEAT=$!

setsid "$@" >> "$LOG" 2>&1
RC=$?

kill "$HEARTBEAT" 2>/dev/null
wait "$HEARTBEAT" 2>/dev/null
if [ "$RC" -eq 0 ]; then write_status completed "$RC"; else write_status failed "$RC"; fi
exit "$RC"
