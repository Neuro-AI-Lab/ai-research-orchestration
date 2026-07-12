#!/usr/bin/env python3
"""Record native Codex lifecycle evidence in the active provider-owned run ledger."""

import json
import os
import re
import sys


ROOT = os.environ.get("CODEX_PROJECT_DIR") or os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, os.path.join(ROOT, ".codex", "scripts"))

from orchestration_audit import (  # noqa: E402
    AuditError,
    append_event,
    bind_subagent_start,
    digest_text,
    safe_role,
    safe_token,
)
from result_contract_gate import validation_error  # noqa: E402


def result_status(message):
    match = re.search(r"(?mi)^\*\*Status:\*\*\s*(complete|partial|blocked|failed)\s*$", message)
    return match.group(1).lower() if match else "missing"


def evidence_count(message):
    return len(re.findall(r"(?m)^\s*-\s*[✅⚠️❌]", message))


def hook_warning(message):
    print(json.dumps({"systemMessage": "Codex orchestration audit warning: " + message}))


def main():
    if not os.environ.get("ORCHESTRATION_RUN_ID"):
        return 0
    try:
        payload = json.load(sys.stdin)
    except Exception:
        hook_warning("hook payload was not valid JSON; this event is unverified")
        return 0
    event = payload.get("hook_event_name")
    try:
        if event == "SessionStart":
            recorded = append_event("session_started", {
                "session_id": safe_token(payload.get("session_id")),
                "source": safe_token(payload.get("source")),
                "model": safe_token(payload.get("model")),
                "permission_mode": safe_token(payload.get("permission_mode")),
                "topology": safe_token(os.environ.get("ORCHESTRATION_TOPOLOGY")),
                "runtime_source": "native_hook",
            })
            run_id = recorded["run_id"]
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": (
                        "Codex orchestration audit is active for {}. Before every native spawn, "
                        "register the exact BRIEF hash with `python3 .codex/scripts/"
                        "orchestration_audit.py brief --role ROLE --dispatch DISPATCH` using the "
                        "BRIEF on stdin. A spawn without prior registration remains unverified."
                    ).format(run_id),
                }
            }))
            return 0
        if event == "SubagentStart":
            role = safe_role(payload.get("agent_type"))
            fields = {
                "session_id": safe_token(payload.get("session_id")),
                "turn_id": safe_token(payload.get("turn_id")),
                "agent_id": safe_token(payload.get("agent_id")),
                "role": role,
                "model": safe_token(payload.get("model")),
                "permission_mode": safe_token(payload.get("permission_mode")),
                "runtime_source": "native_hook",
            }
            recorded, brief_text = bind_subagent_start(fields)
            if brief_text:
                context = (
                    "Native audit identity: agent_id={}; role={}; BRIEF=delivered. The exact "
                    "registered BRIEF below is authoritative for this assignment. End with the "
                    "exact RESULT contract and evidence.\n\n{}"
                ).format(fields["agent_id"], role, brief_text)
            else:
                context = (
                    "Native audit identity: agent_id={}; role={}; BRIEF=missing. Do not perform "
                    "substantive work without a registered BRIEF. Return a blocked RESULT that "
                    "states the missing contract."
                ).format(fields["agent_id"], role)
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "SubagentStart",
                    "additionalContext": context,
                }
            }))
            return 0
        if event == "SubagentStop":
            message = payload.get("last_assistant_message") or ""
            error = validation_error(message)
            append_event("subagent_stopped", {
                "session_id": safe_token(payload.get("session_id")),
                "turn_id": safe_token(payload.get("turn_id")),
                "agent_id": safe_token(payload.get("agent_id")),
                "role": safe_role(payload.get("agent_type")),
                "result_sha256": digest_text(message),
                "result_status": result_status(message),
                "result_contract": "valid" if error is None else "invalid",
                "evidence_count": evidence_count(message),
                "transcript_available": bool(payload.get("agent_transcript_path")),
                "stop_hook_active": bool(payload.get("stop_hook_active")),
                "retained_content": False,
                "runtime_source": "native_hook",
            })
            return 0
    except (AuditError, OSError, ValueError) as exc:
        hook_warning(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
