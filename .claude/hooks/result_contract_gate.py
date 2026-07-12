#!/usr/bin/env python3
"""SubagentStop hook: mechanical enforcement of the RESULT contract.

When a specialist subagent stops, its final message must carry a `## RESULT` block
with all five contract fields (Status, Deliverables, Evidence, Open items, Next) per
.claude/prompts/result-contract.md. A `Status: complete` additionally requires at
least one ✅ evidence line naming an actual check — "complete" without run evidence
is exactly the failure mode this gate exists to bounce.

Scope and safety:
  - Fires only for the eight specialist agent types; the orchestrators report to the
    user in prose, not RESULT form, and unknown/absent agent_type fails open.
  - Bounces at most once: `stop_hook_active` means the agent is already responding
    to a block from this hook, so the retry always passes (never loops).
  - Never crashes the stop: malformed stdin fails open.

This backend owns and validates its contract independently.

Block = print {"decision": "block", "reason": ...} to stdout, exit 0. Allow = exit 0.
"""
import json
import re
import sys

REQUIRED_FIELDS = ("Status", "Deliverables", "Evidence", "Open items", "Next")
SPECIALISTS = {
    "brainstorm", "data", "critic", "developer", "qa",
    "experiment-tracker", "filemanager", "writer",
}


def validation_error(message):
    """Return a bounce reason for a non-conforming final message, else None."""
    marker = re.search(r"(?m)^## RESULT\s*$", message or "")
    if not marker:
        return "Return a final ## RESULT block using .claude/prompts/result-contract.md."
    body = message[marker.end():]
    missing = [field for field in REQUIRED_FIELDS
               if not re.search(r"(?mi)^\*\*" + re.escape(field) + r":\*\*\s*\S", body)]
    if missing:
        return "Complete the RESULT block fields: " + ", ".join(missing) + "."
    status = re.search(r"(?mi)^\*\*Status:\*\*\s*(\S+)", body)
    if status and status.group(1).lower() == "complete":
        if not re.search(r"(?m)^\s*(?:[-*]\s*)?✅", body):
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
    reason = validation_error(payload.get("last_assistant_message") or "")
    if reason:
        print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
