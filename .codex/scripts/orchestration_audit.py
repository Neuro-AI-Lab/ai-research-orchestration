#!/usr/bin/env python3
"""Codex-native orchestration ledger and audit report.

The launcher creates a provider-owned run. Native lifecycle hooks append runtime-issued
session/agent identifiers and RESULT verdicts. Free-form prompts and RESULT bodies are never stored;
the ledger retains hashes and bounded metadata only.
"""

import argparse
import contextlib
import datetime
import hashlib
import json
import os
import re
import sys
import tempfile

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback keeps one-process behavior usable.
    fcntl = None


SCHEMA_VERSION = 2
BACKEND = "codex"
ROLES = {
    "brainstorm", "data", "critic", "developer", "qa", "experiment-tracker",
    "filemanager", "writer",
}
EVENT_TYPES = {
    "session_started", "session_stopped", "brief_registered", "subagent_started",
    "subagent_stopped", "research_gate",
}
RUN_ID = re.compile(r"^ORCH-\d{8}-\d{3,}$")
SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_.:@+-]{1,180}$")
BRIEF_FIELDS = (
    "Dispatch", "Role", "Objective", "Deliverables", "Context", "Constraints",
    "Done when", "Out of scope",
)


class AuditError(Exception):
    pass


def project_root(explicit=None):
    if explicit:
        return os.path.abspath(explicit)
    configured = os.environ.get("CODEX_PROJECT_DIR")
    if configured:
        return os.path.abspath(configured)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def runs_root(root=None):
    return os.path.join(project_root(root), ".codex", "runs")


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def digest_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def safe_token(value):
    if value is None:
        return None
    value = str(value)
    if SAFE_TOKEN.fullmatch(value):
        return value
    return "sha256:" + digest_text(value)[:24]


def safe_role(value):
    value = str(value or "")
    return value if value in ROLES else "unconfigured:" + digest_text(value)[:16]


def atomic_json(path, value):
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".audit-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_text(path, value):
    directory = os.path.dirname(path)
    os.makedirs(directory, mode=0o700, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".brief-", suffix=".tmp", dir=directory, text=True)
    try:
        os.chmod(temporary, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_json(path):
    try:
        with open(path, encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, ValueError) as exc:
        raise AuditError("cannot read {}: {}".format(path, exc))
    if not isinstance(value, dict):
        raise AuditError("{} must contain a JSON object".format(path))
    return value


def run_directory(run_id, root=None):
    if not RUN_ID.fullmatch(str(run_id or "")):
        raise AuditError("invalid run id: {}".format(run_id))
    return os.path.join(runs_root(root), run_id)


@contextlib.contextmanager
def run_lock(directory):
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, ".lock"), "a+", encoding="utf-8") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def read_events(directory):
    path = os.path.join(directory, "events.jsonl")
    events = []
    try:
        with open(path, encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except ValueError as exc:
                    raise AuditError("events.jsonl:{} invalid JSON: {}".format(line_number, exc))
                if not isinstance(event, dict):
                    raise AuditError("events.jsonl:{} is not an object".format(line_number))
                events.append(event)
    except OSError as exc:
        raise AuditError("cannot read events.jsonl: {}".format(exc))
    return events


def chain_errors(events):
    errors = []
    previous = None
    for index, event in enumerate(events, 1):
        if event.get("sequence") != index:
            errors.append("event {} has sequence {}".format(index, event.get("sequence")))
        if event.get("prev_event_hash") != previous:
            errors.append("event {} has an invalid previous hash".format(index))
        claimed = event.get("event_hash")
        body = dict(event)
        body.pop("event_hash", None)
        actual = digest_text(canonical(body))
        if claimed != actual:
            errors.append("event {} hash mismatch".format(index))
        previous = claimed
    return errors


def create_run(fleet, permissions, topology="root-conductor-direct", root=None):
    base = runs_root(root)
    os.makedirs(base, exist_ok=True)
    date = datetime.datetime.now().astimezone().strftime("%Y%m%d")
    for sequence in range(1, 10000):
        run_id = "ORCH-{}-{:03d}".format(date, sequence)
        directory = os.path.join(base, run_id)
        try:
            os.mkdir(directory)
            break
        except FileExistsError:
            continue
    else:
        raise AuditError("daily run id space exhausted")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "backend": BACKEND,
        "fleet": str(fleet),
        "permissions": str(permissions),
        "topology": str(topology),
        "audit_source": "codex-native-hooks",
        "created_at": now(),
        "completed_at": None,
        "status": "launched",
        "root_session_id": None,
        "conductor_orchestrator": "unverified",
        "event_count": 0,
        "event_chain_head": None,
    }
    atomic_json(os.path.join(directory, "manifest.json"), manifest)
    with open(os.path.join(directory, "events.jsonl"), "x", encoding="utf-8"):
        pass
    return {"run_id": run_id, "run_dir": directory}


def active_run_id(explicit=None):
    value = explicit or os.environ.get("ORCHESTRATION_RUN_ID")
    if not value:
        raise AuditError("ORCHESTRATION_RUN_ID is not set; launch through ./orchestrate codex")
    if not RUN_ID.fullmatch(value):
        raise AuditError("invalid ORCHESTRATION_RUN_ID")
    return value


def append_event_locked(directory, manifest, event_type, fields):
    events = read_events(directory)
    errors = chain_errors(events)
    if errors:
        raise AuditError("event chain is invalid: " + "; ".join(errors[:3]))
    previous = events[-1].get("event_hash") if events else None
    fields = dict(fields)
    if event_type == "session_started" and not fields.get("topology"):
        fields["topology"] = manifest.get("topology")
    event = {
        "schema_version": SCHEMA_VERSION,
        "sequence": len(events) + 1,
        "timestamp": now(),
        "run_id": manifest["run_id"],
        "backend": BACKEND,
        "event": event_type,
        "prev_event_hash": previous,
    }
    for key, value in fields.items():
        if key in event or key == "event_hash":
            raise AuditError("reserved event field: {}".format(key))
        event[key] = value
    event["event_hash"] = digest_text(canonical(event))
    with open(os.path.join(directory, "events.jsonl"), "a", encoding="utf-8") as handle:
        handle.write(canonical(event) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    manifest["event_count"] = event["sequence"]
    manifest["event_chain_head"] = event["event_hash"]
    if event_type == "session_started" and not manifest.get("root_session_id"):
        manifest["root_session_id"] = fields.get("session_id")
        manifest["conductor_orchestrator"] = "verified"
        manifest["status"] = "running"
    if (event_type == "session_stopped"
            and fields.get("session_id") == manifest.get("root_session_id")):
        manifest["status"] = "completed"
        manifest["completed_at"] = event["timestamp"]
    atomic_json(os.path.join(directory, "manifest.json"), manifest)
    return event


def append_event(event_type, fields=None, run_id=None, root=None):
    if event_type not in EVENT_TYPES:
        raise AuditError("unsupported event type: {}".format(event_type))
    run_id = active_run_id(run_id)
    directory = run_directory(run_id, root)
    with run_lock(directory):
        manifest = load_json(os.path.join(directory, "manifest.json"))
        if manifest.get("backend") != BACKEND or manifest.get("run_id") != run_id:
            raise AuditError("run manifest identity mismatch")
        return append_event_locked(directory, manifest, event_type, fields or {})


def parse_brief(text):
    if len(text.encode("utf-8")) > 100_000:
        raise AuditError("BRIEF exceeds 100 KB")
    if not re.search(r"(?m)^## BRIEF\s*$", text):
        raise AuditError("BRIEF must start with an exact '## BRIEF' heading")
    values = {}
    for field in BRIEF_FIELDS:
        match = re.search(r"(?mi)^\*\*{}:\*\*\s*(.+)$".format(re.escape(field)), text)
        if not match or not match.group(1).strip() or match.group(1).strip().lower() == "none":
            raise AuditError("BRIEF field is missing or empty: {}".format(field))
        values[field] = match.group(1).strip()
    return values


def register_brief(role, dispatch, text, run_id=None, root=None):
    role = safe_role(role)
    if role.startswith("unconfigured:"):
        raise AuditError("brief role is not configured")
    dispatch = safe_token(dispatch)
    if dispatch is None or dispatch.startswith("sha256:"):
        raise AuditError("dispatch must be a short identifier without spaces")
    values = parse_brief(text)
    if values["Role"] != role:
        raise AuditError("BRIEF Role does not match --role")
    if values["Dispatch"] != dispatch:
        raise AuditError("BRIEF Dispatch does not match --dispatch")
    run_id = active_run_id(run_id)
    directory = run_directory(run_id, root)
    with run_lock(directory):
        manifest = load_json(os.path.join(directory, "manifest.json"))
        events = read_events(directory)
        if any(event.get("event") == "brief_registered" and event.get("dispatch") == dispatch
               for event in events):
            raise AuditError("dispatch is already registered: {}".format(dispatch))
        pending_path = os.path.join(directory, ".pending", dispatch + ".md")
        atomic_text(pending_path, text)
        return append_event_locked(directory, manifest, "brief_registered", {
            "role": role,
            "dispatch": dispatch,
            "brief_sha256": digest_text(text),
            "brief_contract": "valid",
            "retained_content": False,
            "transient_delivery": True,
        })


def pending_brief(role, run_id=None, root=None):
    run_id = active_run_id(run_id)
    events = read_events(run_directory(run_id, root))
    used = {
        event.get("brief_dispatch") for event in events
        if event.get("event") == "subagent_started" and event.get("brief_dispatch")
    }
    for event in events:
        if (event.get("event") == "brief_registered" and event.get("role") == role
                and event.get("dispatch") not in used):
            return event
    return None


def bind_subagent_start(fields, run_id=None, root=None):
    """Atomically bind one queued BRIEF to a native agent and return delivery text."""
    run_id = active_run_id(run_id)
    directory = run_directory(run_id, root)
    role = fields.get("role")
    with run_lock(directory):
        manifest = load_json(os.path.join(directory, "manifest.json"))
        events = read_events(directory)
        used = {
            event.get("brief_dispatch") for event in events
            if event.get("event") == "subagent_started" and event.get("brief_dispatch")
        }
        brief = next((
            event for event in events
            if event.get("event") == "brief_registered" and event.get("role") == role
            and event.get("dispatch") not in used
        ), None)
        brief_text = None
        if brief:
            pending_path = os.path.join(directory, ".pending", brief["dispatch"] + ".md")
            try:
                with open(pending_path, encoding="utf-8") as handle:
                    brief_text = handle.read()
            except OSError:
                brief_text = None
            if brief_text is not None and digest_text(brief_text) != brief.get("brief_sha256"):
                raise AuditError("transient BRIEF hash mismatch for {}".format(brief["dispatch"]))
        bound = brief is not None and brief_text is not None
        fields = dict(fields)
        fields.update({
            "brief_contract": "delivered" if bound else "missing",
            "brief_dispatch": brief.get("dispatch") if bound else None,
            "brief_sha256": brief.get("brief_sha256") if bound else None,
        })
        event = append_event_locked(directory, manifest, "subagent_started", fields)
        if bound:
            os.unlink(os.path.join(directory, ".pending", brief["dispatch"] + ".md"))
        return event, brief_text


def purge_pending(run_id=None, root=None):
    directory = run_directory(active_run_id(run_id), root)
    pending = os.path.join(directory, ".pending")
    try:
        names = os.listdir(pending)
    except OSError:
        return
    for name in names:
        if re.fullmatch(r"[A-Za-z0-9_.:@+-]{1,180}\.md", name):
            try:
                os.unlink(os.path.join(pending, name))
            except OSError:
                pass


def verify_run(target="latest", root=None):
    base = runs_root(root)
    try:
        names = sorted(
            name for name in os.listdir(base)
            if RUN_ID.fullmatch(name) and os.path.isdir(os.path.join(base, name))
        )
    except OSError:
        names = []
    if target == "latest":
        if not names:
            raise AuditError("no Codex orchestration runs found")
        target = names[-1]
    directory = run_directory(target, root)
    manifest = load_json(os.path.join(directory, "manifest.json"))
    events = read_events(directory)
    errors = chain_errors(events)
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("unsupported manifest schema version")
    if any(event.get("schema_version") != SCHEMA_VERSION for event in events):
        errors.append("event schema version mismatch")
    if manifest.get("event_count") != len(events):
        errors.append("manifest event_count mismatch")
    head = events[-1].get("event_hash") if events else None
    if manifest.get("event_chain_head") != head:
        errors.append("manifest event_chain_head mismatch")
    root_id = manifest.get("root_session_id")
    root_starts = [
        event for event in events
        if event.get("event") == "session_started" and event.get("session_id") == root_id
    ]
    root_verified = bool(root_id) and bool(root_starts)
    topology_verified = (
        manifest.get("topology") == "root-conductor-direct"
        and any(event.get("topology") == "root-conductor-direct" for event in root_starts)
    )
    stops = {}
    for event in events:
        if event.get("event") == "subagent_stopped":
            stops[event.get("agent_id")] = event
    specialists = []
    unverified = []
    started_ids = set()
    direct_routing = True
    for event in events:
        if event.get("event") != "subagent_started":
            continue
        native_agent_id = event.get("agent_id")
        stopped = stops.get(native_agent_id, {})
        brief_valid = event.get("brief_contract") == "delivered"
        result_valid = stopped.get("result_contract") == "valid"
        agent_id = native_agent_id or "missing-agent-id"
        parent_valid = bool(root_id) and event.get("session_id") == root_id
        direct_routing = direct_routing and parent_valid
        specialists.append({
            "role": event.get("role"),
            "agent_id": agent_id,
            "parent_session_id": event.get("session_id"),
            "brief": "delivered" if brief_valid else "missing",
            "brief_dispatch": event.get("brief_dispatch"),
            "result": "valid" if result_valid else stopped.get("result_contract", "missing"),
            "result_status": stopped.get("result_status", "missing"),
        })
        if not brief_valid:
            unverified.append("{} has no pre-registered BRIEF".format(agent_id))
        if not result_valid:
            unverified.append("{} has no valid native RESULT".format(agent_id))
        if not native_agent_id:
            unverified.append("specialist start has no native agent ID")
        if not parent_valid:
            unverified.append("{} was not dispatched directly by the root session".format(agent_id))
        if agent_id in started_ids:
            unverified.append("{} has duplicate native start events".format(agent_id))
        started_ids.add(agent_id)
        if stopped and stopped.get("session_id") != root_id:
            unverified.append("{} RESULT is not bound to the root session".format(agent_id))
        if stopped and stopped.get("role") != event.get("role"):
            unverified.append("{} RESULT role does not match its native start".format(agent_id))
    if not root_verified:
        unverified.append("root session was not observed by the native SessionStart hook")
    if not topology_verified:
        unverified.append("root-conductor-direct topology was not verified")
    if manifest.get("status") != "completed":
        unverified.append("root session has not completed")
    registered = {
        event.get("dispatch") for event in events if event.get("event") == "brief_registered"
    }
    delivered = {
        event.get("brief_dispatch") for event in events
        if event.get("event") == "subagent_started" and event.get("brief_dispatch")
    }
    unbound_briefs = sorted(value for value in registered - delivered if value)
    for dispatch in unbound_briefs:
        unverified.append("{} was registered but no native agent started".format(dispatch))
    unverified.extend(errors)
    gate_events = [event for event in events if event.get("event") == "research_gate"]
    allowed_gates = sum(event.get("decision") == "allow" for event in gate_events)
    blocked_gates = sum(event.get("decision") == "block" for event in gate_events)
    return {
        "run_id": manifest.get("run_id", target),
        "backend": manifest.get("backend"),
        "fleet": manifest.get("fleet"),
        "topology": manifest.get("topology"),
        "permissions": manifest.get("permissions"),
        "status": manifest.get("status"),
        "audit_source": manifest.get("audit_source"),
        "event_chain": "verified" if not errors else "invalid",
        "conductor_orchestrator": (
            "verified" if root_verified and topology_verified and direct_routing else "unverified"
        ),
        "specialists": specialists,
        "research_gates": {"allowed": allowed_gates, "blocked": blocked_gates},
        "unverified_claims": len(unverified),
        "verification_errors": unverified,
        "unbound_briefs": unbound_briefs,
        "completed": manifest.get("status") == "completed",
    }


def print_report(report):
    print("Run: {}".format(report["run_id"]))
    print("Backend: {}".format(report["backend"]))
    print("Fleet: {}".format(report["fleet"]))
    print("Topology: {}".format(report["topology"]))
    print("Status: {}".format(report["status"]))
    print("Event chain: {}".format(report["event_chain"]))
    print("Conductor-orchestrator: {}".format(report["conductor_orchestrator"]))
    print("Specialists:")
    if not report["specialists"]:
        print("  none")
    for item in report["specialists"]:
        print("  {role:<18} {agent_id:<38} BRIEF {brief:<7} RESULT {result}".format(**item))
    gates = report["research_gates"]
    print("Research gates: {} allowed, {} blocked".format(gates["allowed"], gates["blocked"]))
    print("Unverified claims: {}".format(report["unverified_claims"]))


def list_runs(root=None):
    base = runs_root(root)
    try:
        names = sorted(
            (name for name in os.listdir(base) if RUN_ID.fullmatch(name)), reverse=True
        )
    except OSError:
        names = []
    rows = []
    for name in names:
        try:
            manifest = load_json(os.path.join(base, name, "manifest.json"))
            rows.append({
                "run_id": name,
                "backend": manifest.get("backend"),
                "fleet": manifest.get("fleet"),
                "status": manifest.get("status"),
                "events": manifest.get("event_count"),
            })
        except AuditError:
            rows.append({"run_id": name, "backend": BACKEND, "fleet": "?",
                         "status": "invalid", "events": "?"})
    return rows


def parser():
    result = argparse.ArgumentParser(description="Codex-native orchestration audit ledger")
    commands = result.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start")
    start.add_argument("--fleet", required=True)
    start.add_argument("--permissions", required=True)
    start.add_argument("--topology", default="root-conductor-direct")
    brief = commands.add_parser("brief")
    brief.add_argument("--role", required=True, choices=sorted(ROLES))
    brief.add_argument("--dispatch", required=True)
    audit = commands.add_parser("audit")
    audit.add_argument("target", nargs="?", default="latest")
    audit.add_argument("--json", action="store_true")
    listing = commands.add_parser("list")
    listing.add_argument("--json", action="store_true")
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    if args.command == "start":
        print(json.dumps(create_run(args.fleet, args.permissions, args.topology), sort_keys=True))
        return 0
    if args.command == "brief":
        text = sys.stdin.read()
        event = register_brief(args.role, args.dispatch, text)
        print("BRIEF registered: {} {} {}".format(
            event["dispatch"], event["role"], event["brief_sha256"]
        ))
        return 0
    if args.command == "audit":
        report = verify_run(args.target)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_report(report)
        return 0 if report["completed"] and report["unverified_claims"] == 0 else 1
    rows = list_runs()
    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    elif not rows:
        print("No Codex orchestration runs found.")
    else:
        print("{:<20} {:<8} {:<10} {:<10} {}".format(
            "RUN", "BACKEND", "FLEET", "STATUS", "EVENTS"
        ))
        for row in rows:
            print("{run_id:<20} {backend:<8} {fleet:<10} {status:<10} {events}".format(**row))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AuditError as exc:
        print("audit: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
