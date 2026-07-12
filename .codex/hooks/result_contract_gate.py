#!/usr/bin/env python3
"""SubagentStop hook enforcing the RESULT contract once without looping."""

import json
import re
import sys


REQUIRED = ("Status", "Deliverables", "Evidence", "Open items", "Next")
SPECIALISTS = {
    "brainstorm", "data", "critic", "developer", "qa",
    "experiment-tracker", "filemanager", "writer",
}


def validation_error(message):
    marker = re.search(r"(?m)^## RESULT\s*$", message or "")
    if not marker:
        return "Return a final ## RESULT block using .codex/contracts/agent-contracts.md."
    result = message[marker.end():]
    missing = [field for field in REQUIRED
               if not re.search(r"(?mi)^\*\*" + re.escape(field) + r":\*\*\s*\S", result)]
    if missing:
        return "Complete the RESULT block fields: " + ", ".join(missing) + "."
    status = re.search(r"(?mi)^\*\*Status:\*\*\s*(\S+)", result)
    if status and status.group(1).lower() == "complete":
        if not re.search(r"(?m)^\s*(?:[-*]\s*)?✅", result):
            return "Status complete requires at least one ✅ evidence line naming an actual check."
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, TypeError):
        return 0
    if payload.get("agent_type") not in SPECIALISTS:
        return 0
    if payload.get("stop_hook_active"):
        return 0
    error = validation_error(payload.get("last_assistant_message") or "")
    if not error:
        return 0
    print(json.dumps({"decision": "block", "reason": error}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
