"""Codex-native run-ledger, identity, privacy, and tamper-evidence tests."""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "codex_orchestration_audit", ROOT / ".codex" / "scripts" / "orchestration_audit.py"
)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


BRIEF = """## BRIEF
**Dispatch:** D001
**Role:** critic
**Objective:** Review the exact plan.
**Deliverables:** REV-001 in the Codex research state.
**Context:** HYP-001 and DATASET-001.
**Constraints:** Do not implement or invent evidence.
**Done when:** The validity checklist has evidence.
**Out of scope:** Code changes and experiment execution.
"""


def complete_fixture(tmp_path):
    created = AUDIT.create_run("quality", "safe", root=tmp_path)
    run_id = created["run_id"]
    AUDIT.append_event(
        "session_started",
        {"session_id": "session-root", "runtime_source": "native_hook"},
        run_id=run_id,
        root=tmp_path,
    )
    AUDIT.register_brief("critic", "D001", BRIEF, run_id=run_id, root=tmp_path)
    _event, delivered = AUDIT.bind_subagent_start(
        {
            "session_id": "session-root", "agent_id": "agent-123", "role": "critic",
            "model": "model-native", "runtime_source": "native_hook",
        },
        run_id=run_id,
        root=tmp_path,
    )
    assert delivered == BRIEF
    AUDIT.append_event(
        "subagent_stopped",
        {
            "session_id": "session-root", "agent_id": "agent-123", "role": "critic",
            "result_contract": "valid", "result_status": "complete",
            "result_sha256": "a" * 64, "runtime_source": "native_hook",
        },
        run_id=run_id,
        root=tmp_path,
    )
    AUDIT.append_event(
        "research_gate",
        {"decision": "allow", "reason_codes": ["all_attestations_passed"]},
        run_id=run_id,
        root=tmp_path,
    )
    AUDIT.finish_run(0, run_id=run_id, root=tmp_path)
    return run_id


def test_complete_native_run_audits_cleanly(tmp_path):
    run_id = complete_fixture(tmp_path)
    report = AUDIT.verify_run(run_id, root=tmp_path)
    assert report["event_chain"] == "verified"
    assert report["conductor_orchestrator"] == "verified"
    assert report["status"] == "completed"
    assert report["unverified_claims"] == 0
    assert report["specialists"] == [{
        "role": "critic",
        "model": "model-native",
        "agent_id": "agent-123",
        "parent_session_id": "session-root",
        "brief": "delivered",
        "brief_dispatch": "D001",
        "result": "valid",
        "result_status": "complete",
    }]
    assert report["research_gates"] == {"allowed": 1, "blocked": 0}


def test_missing_brief_and_result_remain_unverified(tmp_path):
    created = AUDIT.create_run("quality", "safe", root=tmp_path)
    run_id = created["run_id"]
    AUDIT.append_event(
        "session_started", {"session_id": "root"}, run_id=run_id, root=tmp_path
    )
    AUDIT.append_event(
        "subagent_started",
        {"session_id": "root", "agent_id": "agent-x", "role": "developer",
         "brief_contract": "missing"},
        run_id=run_id,
        root=tmp_path,
    )
    report = AUDIT.verify_run(run_id, root=tmp_path)
    assert report["unverified_claims"] == 3
    assert report["specialists"][0]["brief"] == "missing"
    assert report["specialists"][0]["result"] == "missing"


def test_non_root_dispatch_and_mismatched_result_role_are_unverified(tmp_path):
    created = AUDIT.create_run("quality", "safe", root=tmp_path)
    run_id = created["run_id"]
    AUDIT.append_event(
        "session_started", {"session_id": "root"}, run_id=run_id, root=tmp_path
    )
    AUDIT.register_brief("critic", "D001", BRIEF, run_id=run_id, root=tmp_path)
    AUDIT.bind_subagent_start(
        {"session_id": "nested-session", "agent_id": "agent-nested", "role": "critic"},
        run_id=run_id, root=tmp_path,
    )
    AUDIT.append_event(
        "subagent_stopped",
        {"session_id": "nested-session", "agent_id": "agent-nested", "role": "data",
         "result_contract": "valid", "result_status": "complete"},
        run_id=run_id, root=tmp_path,
    )
    AUDIT.finish_run(0, run_id=run_id, root=tmp_path)
    report = AUDIT.verify_run(run_id, root=tmp_path)
    assert report["conductor_orchestrator"] == "unverified"
    assert any("not dispatched directly" in item for item in report["verification_errors"])
    assert any("RESULT role does not match" in item for item in report["verification_errors"])


def test_codex_audit_rejects_an_orchestrator_subagent_brief(tmp_path):
    created = AUDIT.create_run("quality", "safe", root=tmp_path)
    with pytest.raises(AUDIT.AuditError):
        AUDIT.register_brief(
            "orchestrator", "D001", BRIEF.replace("**Role:** critic", "**Role:** orchestrator"),
            run_id=created["run_id"], root=tmp_path,
        )


def test_event_edit_breaks_hash_chain(tmp_path):
    run_id = complete_fixture(tmp_path)
    event_path = tmp_path / ".codex" / "runs" / run_id / "events.jsonl"
    events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()]
    events[0]["session_id"] = "forged-session"
    event_path.write_text(
        "\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n",
        encoding="utf-8",
    )
    report = AUDIT.verify_run(run_id, root=tmp_path)
    assert report["event_chain"] == "invalid"
    assert any("hash mismatch" in error for error in report["verification_errors"])


def test_brief_content_is_hashed_not_retained(tmp_path):
    created = AUDIT.create_run("quality", "safe", root=tmp_path)
    secret_marker = "PRIVATE-HYPOTHESIS-DO-NOT-RETAIN"
    brief = BRIEF.replace("Review the exact plan.", "Review " + secret_marker + ".")
    AUDIT.register_brief(
        "critic", "D001", brief, run_id=created["run_id"], root=tmp_path
    )
    _event, delivered = AUDIT.bind_subagent_start(
        {"session_id": "root", "agent_id": "agent-private", "role": "critic"},
        run_id=created["run_id"], root=tmp_path,
    )
    assert secret_marker in delivered
    ledger = (
        tmp_path / ".codex" / "runs" / created["run_id"] / "events.jsonl"
    ).read_text(encoding="utf-8")
    assert secret_marker not in ledger
    assert AUDIT.digest_text(brief) in ledger
    assert not list((
        tmp_path / ".codex" / "runs" / created["run_id"] / ".pending"
    ).glob("*.md"))


def test_unsafe_runtime_identifier_is_reduced_to_hash():
    value = AUDIT.safe_token("agent id with a secret/token/path")
    assert value.startswith("sha256:")
    assert "secret" not in value


def test_native_hook_payload_binds_identity_and_result(tmp_path):
    scripts = tmp_path / ".codex" / "scripts"
    scripts.mkdir(parents=True)
    os.symlink(ROOT / ".codex" / "scripts" / "orchestration_audit.py",
               scripts / "orchestration_audit.py")
    created = AUDIT.create_run("quality", "safe", root=tmp_path)
    run_id = created["run_id"]
    env = dict(
        os.environ,
        CODEX_PROJECT_DIR=str(tmp_path),
        ORCHESTRATION_RUN_ID=run_id,
        ORCHESTRATION_RUN_DIR=created["run_dir"],
    )
    hook = ROOT / ".codex" / "hooks" / "audit_event.py"

    def invoke(payload):
        return subprocess.run(
            [sys.executable, str(hook)], input=json.dumps(payload), text=True,
            capture_output=True, env=env, check=False,
        )

    started = invoke({
        "hook_event_name": "SessionStart", "session_id": "session-native",
        "source": "startup", "model": "model-native", "permission_mode": "default",
    })
    assert started.returncode == 0, started.stderr
    assert "audit is active" in started.stdout
    AUDIT.register_brief("critic", "D001", BRIEF, run_id=run_id, root=tmp_path)
    child = invoke({
        "hook_event_name": "SubagentStart", "session_id": "session-native",
        "turn_id": "turn-1", "agent_id": "agent-native-1", "agent_type": "critic",
        "model": "model-native", "permission_mode": "default",
    })
    assert child.returncode == 0, child.stderr
    assert "agent-native-1" in child.stdout
    result = """## RESULT
**Status:** complete
**Deliverables:** REV-001
**Evidence:**
- ✅ exact review command passed
**Open items:** none
**Next:** none
"""
    stopped = invoke({
        "hook_event_name": "SubagentStop", "session_id": "session-native",
        "turn_id": "turn-1", "agent_id": "agent-native-1", "agent_type": "critic",
        "last_assistant_message": result, "agent_transcript_path": "/private/transcript",
        "stop_hook_active": False,
    })
    assert stopped.returncode == 0, stopped.stderr
    research = tmp_path / "report"
    research.mkdir(parents=True)
    (research / "discussion.md").write_text(
        """## [DATASET-001] fixture
**Leakage audit:** passed
## [REV-001] plan gate
**Gate:** passed
**Status:** resolved
## [QA-001] code gate
**Gate:** passed
**Status:** complete
""",
        encoding="utf-8",
    )
    (research / "issue.md").write_text("# no open issues\n", encoding="utf-8")
    gate = subprocess.run(
        [sys.executable, str(ROOT / ".codex" / "hooks" / "experiment_gate.py")],
        input=json.dumps({
            "hook_event_name": "PreToolUse", "session_id": "session-native",
            "turn_id": "turn-run", "tool_use_id": "tool-run", "tool_name": "Bash",
            "tool_input": {"command": "./run.sh train"},
        }),
        text=True, capture_output=True, env=env, check=False,
    )
    assert gate.returncode == 0, gate.stderr
    closed = subprocess.run(
        [sys.executable, str(ROOT / ".codex" / "hooks" / "session_close_gate.py")],
        input=json.dumps({
            "hook_event_name": "Stop", "session_id": "session-native",
            "turn_id": "turn-root", "last_assistant_message": "complete",
            "stop_hook_active": False,
        }),
        text=True, capture_output=True, env=env, check=False,
    )
    assert closed.returncode == 0, closed.stderr
    AUDIT.finish_run(0, run_id=run_id, root=tmp_path)
    report = AUDIT.verify_run(run_id, root=tmp_path)
    assert report["unverified_claims"] == 0
    assert report["specialists"][0]["agent_id"] == "agent-native-1"
    assert report["research_gates"] == {"allowed": 1, "blocked": 0}
    ledger = (
        tmp_path / ".codex" / "runs" / run_id / "events.jsonl"
    ).read_text(encoding="utf-8")
    assert "/private/transcript" not in ledger


def test_audit_cli_text_json_and_list(tmp_path):
    run_id = complete_fixture(tmp_path)
    script = ROOT / ".codex" / "scripts" / "orchestration_audit.py"
    env = dict(os.environ, CODEX_PROJECT_DIR=str(tmp_path))
    text_report = subprocess.run(
        [sys.executable, str(script), "audit", "latest"], text=True,
        capture_output=True, env=env, check=False,
    )
    assert text_report.returncode == 0, text_report.stderr
    assert "Run: " + run_id in text_report.stdout
    assert "critic" in text_report.stdout
    assert "agent-123" in text_report.stdout
    assert "Unverified claims: 0" in text_report.stdout
    json_report = subprocess.run(
        [sys.executable, str(script), "audit", run_id, "--json"], text=True,
        capture_output=True, env=env, check=False,
    )
    assert json_report.returncode == 0, json_report.stderr
    assert json.loads(json_report.stdout)["conductor_orchestrator"] == "verified"
    listing = subprocess.run(
        [sys.executable, str(script), "list"], text=True,
        capture_output=True, env=env, check=False,
    )
    assert listing.returncode == 0, listing.stderr
    assert run_id in listing.stdout


def test_stale_handoff_stop_is_nonblocking_and_audited(tmp_path):
    scripts = tmp_path / ".codex" / "scripts"
    scripts.mkdir(parents=True)
    os.symlink(ROOT / ".codex" / "scripts" / "orchestration_audit.py",
               scripts / "orchestration_audit.py")
    created = AUDIT.create_run("quality", "safe", root=tmp_path)
    run_id = created["run_id"]
    AUDIT.append_event(
        "session_started", {"session_id": "root-stop"}, run_id=run_id, root=tmp_path
    )
    state = tmp_path / ".codex" / "state"
    research = tmp_path / "report"
    state.mkdir(parents=True)
    research.mkdir(parents=True)
    handoff = state / "handoff.json"
    discussion = research / "discussion.md"
    handoff.write_text("{}\n", encoding="utf-8")
    discussion.write_text("changed\n", encoding="utf-8")
    os.utime(handoff, (1, 1))
    os.utime(discussion, (2, 2))
    env = dict(
        os.environ, CODEX_PROJECT_DIR=str(tmp_path), ORCHESTRATION_RUN_ID=run_id,
        ORCHESTRATION_RUN_DIR=created["run_dir"],
    )
    hook = ROOT / ".codex" / "hooks" / "session_close_gate.py"

    def stop(active):
        return subprocess.run(
            [sys.executable, str(hook)], input=json.dumps({
                "hook_event_name": "Stop", "session_id": "root-stop", "turn_id": "turn-stop",
                "last_assistant_message": "done", "stop_hook_active": active,
            }), text=True, capture_output=True, env=env, check=False,
        )

    first = stop(False)
    assert first.returncode == 0
    assert first.stdout == ""
    assert AUDIT.verify_run(run_id, root=tmp_path)["status"] == "running"
    ledger = (
        tmp_path / ".codex" / "runs" / run_id / "events.jsonl"
    ).read_text(encoding="utf-8")
    assert '"continuity_current":false' in ledger
    assert '"event":"turn_stopped"' in ledger
    assert '"event":"session_ended"' not in ledger
    AUDIT.finish_run(0, run_id=run_id, root=tmp_path)
    assert AUDIT.verify_run(run_id, root=tmp_path)["status"] == "completed"


def test_failed_process_exit_is_ended_but_not_verified_complete(tmp_path):
    created = AUDIT.create_run("quality", "safe", root=tmp_path)
    run_id = created["run_id"]
    AUDIT.append_event(
        "session_started", {"session_id": "root-failed"}, run_id=run_id, root=tmp_path
    )
    AUDIT.finish_run(7, run_id=run_id, root=tmp_path)
    report = AUDIT.verify_run(run_id, root=tmp_path)
    assert report["status"] == "failed"
    assert report["completed"] is False
    assert any("exited with code 7" in item for item in report["verification_errors"])
    with pytest.raises(AUDIT.AuditError, match="ended run"):
        AUDIT.append_event(
            "turn_stopped", {"session_id": "root-failed"}, run_id=run_id, root=tmp_path
        )


def test_session_brief_hook_emits_valid_start_json(tmp_path):
    hook = ROOT / ".codex" / "hooks" / "session_brief.py"
    env = dict(os.environ, CODEX_PROJECT_DIR=str(tmp_path))
    proc = subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps({"hook_event_name": "SessionStart"}),
        text=True, capture_output=True, env=env, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    output = json.loads(proc.stdout)
    specific = output["hookSpecificOutput"]
    assert specific["hookEventName"] == "SessionStart"
    assert "Automatic continuity brief" in specific["additionalContext"]

    child = subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps({"hook_event_name": "SubagentStart"}),
        text=True, capture_output=True, env=env, check=False,
    )
    assert json.loads(child.stdout)["hookSpecificOutput"]["hookEventName"] == "SubagentStart"
