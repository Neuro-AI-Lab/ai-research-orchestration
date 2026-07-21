#!/usr/bin/env python3
"""Researcher-facing launcher for the Claude and Codex orchestration stacks."""

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_CONFIG = os.path.join(ROOT, ".orchestration", "config.local.json")
CACHE_DIR = os.path.join(ROOT, ".codex", "cache", "agents")
CODEX_AUDIT = os.path.join(ROOT, ".codex", "scripts", "orchestration_audit.py")
CODEX_ROLES = (
    "brainstorm", "data", "critic", "developer", "qa",
    "experiment-tracker", "filemanager", "writer",
)
CODEX_MCP_SERVERS = {
    "literature": {
        "command": "python3",
        "args": [".codex/scripts/literature_mcp.py"],
        "tools": {"lit_search", "lit_fetch"},
    },
    "zotero": {
        "command": "python3",
        "args": [".codex/scripts/zotero_mcp.py", "serve"],
        "tools": {
            "zotero_search", "zotero_item", "zotero_fulltext", "zotero_bibtex",
            "zotero_collections", "zotero_add",
        },
    },
}
PRESETS = {
    "quality": ("gpt-5.6-sol", "xhigh"),
    "balanced": ("gpt-5.6-sol", "high"),
    "fast": ("gpt-5.6-terra", "medium"),
}
EFFORTS = {"minimal", "low", "medium", "high", "xhigh", "max", "ultra"}

# Claude fleet system. Same preset names as Codex, but resolved only from Claude-owned
# JSON manifests and agent definitions. Claude keeps its own lead-agent roles; Codex has
# no lead subagent because the root Codex session is the conductor-orchestrator.
CLAUDE_FLEET_DIR = os.path.join(ROOT, ".claude", "fleets")
CLAUDE_AGENT_DIR = os.path.join(ROOT, ".claude", "agents")
CLAUDE_SPECIALIST_ROLES = (
    "brainstorm", "data", "critic", "developer", "qa",
    "experiment-tracker", "filemanager", "writer",
)
CLAUDE_CORE_ROLES = ("orchestrator",) + CLAUDE_SPECIALIST_ROLES
CLAUDE_ROLES = CLAUDE_CORE_ROLES + ("orchestrator-opus",)
OVERRIDE_ROLES = (
    "orchestrator", "brainstorm", "data", "critic", "developer", "qa",
    "experiment-tracker", "filemanager", "writer",
)
CLAUDE_MODELS = {"fable", "opus", "sonnet", "haiku"}
CLAUDE_EFFORTS = {"low", "medium", "high", "xhigh", "max"}
CLAUDE_MODEL_RANK = {"haiku": 0, "sonnet": 1, "opus": 2, "fable": 3}
CLAUDE_EFFORT_RANK = {"low": 0, "medium": 1, "high": 2, "xhigh": 3, "max": 4}
CLAUDE_LEAD_MODELS = {"fable", "opus"}
# Research-gate floors: no preset or override may weaken the verification chain.
# Permissions posture is orthogonal and never affects these.
CLAUDE_FLOORS = {
    "critic": ("sonnet", "high"),
    "qa": ("sonnet", "high"),
    "data": ("sonnet", "medium"),
}


class LaunchError(Exception):
    pass


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as handle:
            value = json.load(handle)
        return value if isinstance(value, dict) else default
    except (OSError, ValueError):
        return default


def choose(label, options, default=None):
    if not sys.stdin.isatty():
        raise LaunchError("No saved backend and stdin is non-interactive; pass 'codex' or 'claude'.")
    print(label)
    for index, option in enumerate(options, 1):
        suffix = " (default)" if option == default else ""
        print("  {}. {}{}".format(index, option, suffix))
    raw = input("> ").strip()
    if not raw and default:
        return default
    try:
        return options[int(raw) - 1]
    except (ValueError, IndexError):
        if raw in options:
            return raw
        raise LaunchError("Invalid selection: {}".format(raw))


def parse_override(text):
    if "=" not in text:
        raise LaunchError("Role override must be ROLE=PRESET or ROLE=MODEL@EFFORT: {}".format(text))
    role, value = text.split("=", 1)
    if role not in OVERRIDE_ROLES:
        raise LaunchError(
            "Unknown role '{}'; choose from {}.".format(role, ", ".join(OVERRIDE_ROLES))
        )
    if value in PRESETS:
        return role, value
    if "@" not in value:
        raise LaunchError("Custom role override must include @EFFORT: {}".format(text))
    model, effort = value.rsplit("@", 1)
    if not model or effort not in EFFORTS:
        raise LaunchError("Invalid model/effort override: {}".format(text))
    return role, {"model": model, "effort": effort}


def agent_path(preset, role):
    return os.path.join(ROOT, ".codex", "fleets", preset, role + ".toml")


def custom_agent_path(role, model, effort):
    source = agent_path("quality", role)
    with open(source, encoding="utf-8") as handle:
        content = handle.read()
    content = re.sub(r'(?m)^model = ".*"$', 'model = "{}"'.format(model), content)
    content = re.sub(
        r'(?m)^model_reasoning_effort = ".*"$',
        'model_reasoning_effort = "{}"'.format(effort), content,
    )
    digest = hashlib.sha256((role + "\0" + model + "\0" + effort).encode("utf-8")).hexdigest()[:12]
    os.makedirs(CACHE_DIR, exist_ok=True)
    destination = os.path.join(CACHE_DIR, "{}-{}.toml".format(role, digest))
    temporary = destination + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        handle.write(content)
    os.replace(temporary, destination)
    return destination


def codex_catalog():
    proc = subprocess.run(
        ["codex", "debug", "models", "--bundled"], cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )
    if proc.returncode:
        raise LaunchError("Could not read the installed Codex model catalog: " + proc.stderr.strip())
    try:
        models = json.loads(proc.stdout).get("models", [])
    except ValueError as exc:
        raise LaunchError("Installed Codex returned an invalid model catalog: {}".format(exc))
    return {
        item.get("slug"): {level.get("effort") for level in item.get("supported_reasoning_levels", [])}
        for item in models if item.get("slug")
    }


def model_from_agent_file(path):
    with open(path, encoding="utf-8") as handle:
        content = handle.read()
    model = re.search(r'(?m)^model = "([^"]+)"$', content)
    effort = re.search(r'(?m)^model_reasoning_effort = "([^"]+)"$', content)
    if not model or not effort:
        raise LaunchError("Agent config lacks model settings: " + path)
    return model.group(1), effort.group(1)


def validate_codex(agent_files, root_model, root_effort):
    if not shutil.which("codex"):
        raise LaunchError("Codex CLI is not installed or not on PATH.")
    features = subprocess.run(
        ["codex", "features", "list"], cwd=ROOT, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, check=False,
    )
    if features.returncode or not all(name in features.stdout for name in ("multi_agent", "hooks")):
        raise LaunchError("This Codex installation does not expose multi_agent and hooks; update Codex.")
    catalog = codex_catalog()
    requested = [("root", root_model, root_effort)]
    requested.extend((role,) + model_from_agent_file(path) for role, path in agent_files.items())
    errors = []
    for role, model, effort in requested:
        if model not in catalog:
            errors.append("{}: model {} is unavailable".format(role, model))
        elif effort not in catalog[model]:
            errors.append("{}: {} does not support effort {}".format(role, model, effort))
    if errors:
        raise LaunchError("Invalid Codex fleet:\n  - " + "\n  - ".join(errors))


def validate_codex_mcp():
    """Verify project config, optional trusted-project loading, and STDIO discovery."""
    if not shutil.which("codex"):
        raise LaunchError("Codex CLI is not installed or not on PATH.")
    try:
        with open(os.path.join(ROOT, ".codex", "config.toml"), encoding="utf-8") as handle:
            config_text = handle.read()
    except OSError as exc:
        raise LaunchError("Cannot read Codex project MCP configuration: {}".format(exc))
    requests = "\n".join((
        json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05", "capabilities": {},
                "clientInfo": {"name": "orchestrate-doctor", "version": "1"},
            },
        }),
        json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
    )) + "\n"
    errors = []
    loaded = []
    for name, expected in CODEX_MCP_SERVERS.items():
        block_match = re.search(
            r"(?ms)^\[mcp_servers\.{}\]\s*\n(.*?)(?=^\[|\Z)".format(re.escape(name)),
            config_text,
        )
        block = block_match.group(1) if block_match else ""
        command_match = re.search(r'(?m)^command\s*=\s*"([^"]+)"\s*$', block)
        args_match = re.search(r"(?m)^args\s*=\s*(\[[^\n]+\])\s*$", block)
        try:
            configured_args = json.loads(args_match.group(1)) if args_match else None
        except ValueError:
            configured_args = None
        if not (
            command_match and command_match.group(1) == expected["command"]
            and configured_args == expected["args"]
        ):
            errors.append("{}: .codex/config.toml registration mismatch".format(name))

        registered = subprocess.run(
            ["codex", "mcp", "get", name, "--json"], cwd=ROOT,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        )
        if registered.returncode == 0:
            try:
                config = json.loads(registered.stdout)
            except ValueError:
                config = {}
            if not isinstance(config, dict):
                config = {}
            transport = config.get("transport", {})
            if not (
                config.get("enabled") is True
                and transport.get("type") == "stdio"
                and transport.get("command") == expected["command"]
                and transport.get("args") == expected["args"]
            ):
                errors.append("{}: loaded project registration mismatch".format(name))
            loaded.append(True)
        elif "No MCP server named" in registered.stderr:
            # A fresh checkout does not load project MCP until the user trusts the repository.
            loaded.append(False)
        else:
            detail = registered.stderr.strip() or registered.stdout.strip() or "unknown CLI error"
            errors.append("{}: cannot inspect project registration ({})".format(name, detail))
            loaded.append(False)

        command = [expected["command"]] + expected["args"]
        try:
            handshake = subprocess.run(
                command, cwd=ROOT, input=requests, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, timeout=10, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append("{}: STDIO handshake failed ({})".format(name, exc))
            continue
        responses = []
        try:
            responses = [json.loads(line) for line in handshake.stdout.splitlines() if line.strip()]
        except ValueError as exc:
            errors.append("{}: invalid JSON-RPC response ({})".format(name, exc))
            continue
        listing = next((item for item in responses if item.get("id") == 2), {})
        tools = {
            item.get("name") for item in listing.get("result", {}).get("tools", [])
            if isinstance(item, dict) and item.get("name")
        }
        if handshake.returncode or tools != expected["tools"]:
            detail = handshake.stderr.strip() or "tools={}".format(",".join(sorted(tools)))
            errors.append("{}: STDIO tool set mismatch ({})".format(name, detail))
    if any(loaded) and not all(loaded):
        errors.append("project MCP registration is only partially loaded")
    if errors:
        raise LaunchError("Invalid Codex MCP integration:\n  - " + "\n  - ".join(errors))
    return {
        "tools": {name: sorted(spec["tools"]) for name, spec in CODEX_MCP_SERVERS.items()},
        "project_config_loaded": all(loaded),
    }


def load_backend_env(backend=None, preset=None, permissions=None, audit_run=None):
    env = os.environ.copy()
    settings_path = os.path.join(ROOT, ".{}".format(backend), "settings.local.json")
    settings = read_json(settings_path, {}) if backend else {}
    for key, value in settings.get("env", {}).items():
        if not key.startswith("_") and isinstance(value, str) and value:
            env[key] = value
    if backend:
        env["ORCHESTRATION_BACKEND"] = backend
    if preset:
        env["ORCHESTRATION_FLEET"] = preset
    if permissions:
        env["ORCHESTRATION_PERMISSIONS"] = permissions
    if audit_run:
        env["ORCHESTRATION_RUN_ID"] = audit_run["run_id"]
        env["ORCHESTRATION_RUN_DIR"] = audit_run["run_dir"]
    env["ORCHESTRATION_TOPOLOGY"] = (
        "root-conductor-direct" if backend == "codex" else "adaptive-direct"
    )
    return env


def initialize_project(backend):
    if backend not in ("codex", "claude"):
        raise LaunchError("init requires exactly one backend: codex or claude")
    pairs = (
        (".{0}/settings.local.json.example".format(backend),
         ".{0}/settings.local.json".format(backend)),
        (".{0}/state/handoff.json.example".format(backend),
         ".{0}/state/handoff.json".format(backend)),
    )
    for source, destination in pairs:
        source_path = os.path.join(ROOT, source)
        destination_path = os.path.join(ROOT, destination)
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        if os.path.exists(destination_path):
            print("exists  " + destination)
        else:
            shutil.copyfile(source_path, destination_path)
            print("created " + destination)
    for name in ("discussion.md", "result.md", "error.md", "version.md"):
        relative = ".{}/research/{}".format(backend, name)
        destination = os.path.join(ROOT, relative)
        if not os.path.exists(destination):
            source = os.path.join(ROOT, ".{}".format(backend), "templates", "research", name)
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.copyfile(source, destination)
            print("created " + relative)

    memory_root = "memory" if backend == "codex" else "agent-memory"
    memory_roles = ("conductor", "brainstorm", "critic") if backend == "codex" else (
        "orchestrator", "brainstorm", "critic"
    )
    for role in memory_roles:
        relative = ".{}/{}/{}/MEMORY.md".format(backend, memory_root, role)
        destination = os.path.join(ROOT, relative)
        if not os.path.exists(destination):
            source = os.path.join(
                ROOT, ".{}".format(backend), "templates", "memory", role, "MEMORY.md"
            )
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.copyfile(source, destination)
            print("created " + relative)

    for name in (
            "data", "models", "evaluation", "papers/notes/{}".format(backend),
            "experiments/{}".format(backend), "analysis/{}".format(backend),
            ".{}/runs".format(backend)):
        os.makedirs(os.path.join(ROOT, name), exist_ok=True)
    print(
        "{} initialization complete. Run './orchestrate doctor {}', then "
        "'./orchestrate {}'.".format(backend.capitalize(), backend, backend)
    )
    return 0


def doctor(backend):
    if backend not in ("codex", "claude"):
        raise LaunchError("doctor requires exactly one backend: codex or claude")
    failures = []
    warnings = []

    def report(status, name, detail):
        print("{:<5} {:<28} {}".format(status, name, detail))

    provider_required = {
        "codex": (
            "AGENTS.md", ".codex/README.md", ".codex/ORCHESTRATION.md",
            ".codex/config.toml", ".codex/hooks/audit_event.py",
            ".codex/scripts/orchestration_audit.py", ".codex/settings.local.json",
            ".codex/state/handoff.json", ".codex/memory/conductor/MEMORY.md",
        ),
        "claude": (
            "CLAUDE.md", ".mcp.json", ".claude/README.md", ".claude/settings.json",
            ".claude/settings.local.json", ".claude/state/handoff.json",
            ".claude/agent-memory/orchestrator/MEMORY.md",
        ),
    }
    required = provider_required[backend] + tuple(
        ".{}/research/{}".format(backend, name)
        for name in ("discussion.md", "result.md", "error.md", "version.md")
    )
    for path in required:
        if os.path.isfile(os.path.join(ROOT, path)):
            report("PASS", path, "present")
        else:
            report("FAIL", path, "missing")
            failures.append(path + " is missing")

    for path in ("orchestrate", "setup.sh", "run.sh", "evaluate.sh"):
        full = os.path.join(ROOT, path)
        if os.path.isfile(full) and os.path.getsize(full) > 0 and os.access(full, os.X_OK):
            report("PASS", path, "non-empty and executable")
        else:
            report("FAIL", path, "must be non-empty and executable")
            failures.append(path + " is not a usable entrypoint")

    if sys.version_info >= (3, 8):
        report("PASS", "Python", sys.version.split()[0])
    else:
        report("FAIL", "Python", "3.8+ required")
        failures.append("Python 3.8+ is required")

    for binary in ("git", backend):
        path = shutil.which(binary)
        if path:
            report("PASS", binary, path)
        else:
            report("FAIL", binary, "not found")
            failures.append(binary + " is required for the selected backend")
    if shutil.which("setsid"):
        report("PASS", "setsid", "long-run process isolation available")
    else:
        report("WARN", "setsid", "long-run wrapper may require Linux/WSL or a compatible tool")
        warnings.append("setsid is unavailable")

    json_paths = [
        ".orchestration/config.local.json.example",
        ".{0}/settings.local.json.example".format(backend),
        ".{0}/state/handoff.json.example".format(backend),
        ".{0}/settings.local.json".format(backend),
        ".{0}/state/handoff.json".format(backend),
    ]
    if backend == "claude":
        json_paths.extend((".mcp.json", ".claude/settings.json"))
    for path in json_paths:
        try:
            with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
                json.load(handle)
            report("PASS", path, "valid JSON")
        except (OSError, ValueError) as exc:
            report("FAIL", path, str(exc))
            failures.append(path + " is invalid")

    if backend == "codex":
        try:
            with open(os.path.join(ROOT, ".codex", "config.toml"), encoding="utf-8") as handle:
                config_text = handle.read()
            structural = (
                re.search(r"(?m)^max_depth\s*=\s*1\s*$", config_text) is not None
                and re.search(r"(?m)^max_threads\s*=\s*4\s*$", config_text) is not None
                and "[agents.orchestrator]" not in config_text
                and all(os.path.isfile(agent_path(preset_name, role))
                        for preset_name in PRESETS for role in CODEX_ROLES)
                and not any(os.path.exists(agent_path(preset_name, "orchestrator"))
                            for preset_name in PRESETS)
            )
            if not structural:
                raise LaunchError(
                    "Codex must be a depth-1 root conductor-orchestrator with four-thread "
                    "bounded concurrency and eight specialists"
                )
            report("PASS", "Codex topology", "root conductor; depth 1; 4 threads; 8 roles")
            files = {role: agent_path("quality", role) for role in CODEX_ROLES}
            validate_codex(files, *PRESETS["quality"])
            report("PASS", "Codex quality fleet", "models, efforts, hooks, multi_agent")
        except (OSError, LaunchError) as exc:
            report("FAIL", "Codex control plane", str(exc))
            failures.append(str(exc))
        try:
            mcp = validate_codex_mcp()
            detail = ", ".join(
                "{}({})".format(name, len(names))
                for name, names in sorted(mcp["tools"].items())
            )
            report("PASS", "Codex MCP", detail + "; config and STDIO handshake")
            activation = (
                "loaded by trusted project"
                if mcp["project_config_loaded"]
                else "pending first project trust/restart"
            )
            report("INFO", "Codex MCP activation", activation)
        except LaunchError as exc:
            report("FAIL", "Codex MCP", str(exc))
            failures.append(str(exc))
    else:
        try:
            for preset_name in PRESETS:
                validate_claude_fleet(claude_fleet(preset_name))
            claude_quality_drift()
            report("PASS", "Claude fleets", "manifests and agent frontmatter agree")
        except LaunchError as exc:
            report("FAIL", "Claude fleets", str(exc))
            failures.append(str(exc))

    settings = read_json(os.path.join(ROOT, ".{}".format(backend), "settings.local.json"), {})
    configured = sorted(
        key for key, value in settings.get("env", {}).items()
        if not key.startswith("_") and isinstance(value, str) and value
    )
    report("INFO", backend + " optional env", ", ".join(configured) if configured else "none")

    isolation = subprocess.run(
        [sys.executable, os.path.join(ROOT, ".orchestration", "isolation.py")],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )
    if isolation.returncode:
        detail = isolation.stdout.strip() or isolation.stderr.strip() or "unknown failure"
        report("FAIL", "Provider isolation", detail.splitlines()[-1])
        failures.append(detail)
    else:
        report("PASS", "Provider isolation", "static control-plane boundary verified")

    store = ".{}/runs/probe.json".format(backend)
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", store], cwd=ROOT, check=False
    ).returncode == 0
    if ignored:
        report("PASS", backend + " runtime store", "ignored and provider-owned")
    else:
        report("FAIL", backend + " runtime store", "must be ignored")
        failures.append(store + " is distribution-visible")

    print("\nDoctor [{}]: {} failure(s), {} warning(s)".format(
        backend, len(failures), len(warnings)
    ))
    return 1 if failures else 0


def run_demo():
    commands = (
        [sys.executable, "examples/toy-sentiment/verify_split.py"],
        [sys.executable, "examples/toy-sentiment/run_example.py"],
    )
    for command in commands:
        print("+ " + shlex.join(command), flush=True)
        proc = subprocess.run(command, cwd=ROOT, check=False)
        if proc.returncode:
            return proc.returncode
    print("Demo complete: split verification and end-to-end run passed.")
    return 0


def release_check():
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, ".orchestration", "release_check.py")],
        cwd=ROOT, check=False,
    ).returncode


def codex_audit(arguments, capture=False):
    proc = subprocess.run(
        [sys.executable, CODEX_AUDIT] + list(arguments), cwd=ROOT, check=False,
        text=True, stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if capture and proc.returncode:
        raise LaunchError((proc.stderr or proc.stdout or "Codex audit command failed").strip())
    return proc


def start_codex_audit(preset, permissions):
    proc = codex_audit(
        ["start", "--fleet", preset, "--permissions", permissions,
         "--topology", "root-conductor-direct"],
        capture=True,
    )
    try:
        result = json.loads(proc.stdout)
    except (TypeError, ValueError) as exc:
        raise LaunchError("Codex audit launcher returned invalid JSON: {}".format(exc))
    if not all(isinstance(result.get(key), str) and result.get(key)
               for key in ("run_id", "run_dir")):
        raise LaunchError("Codex audit launcher omitted run identity")
    return result


def confirm_bypass(allowed):
    if allowed:
        return
    if not sys.stdin.isatty():
        raise LaunchError("Bypass requires --allow-unsafe-bypass in non-interactive use.")
    print("WARNING: bypass removes local filesystem/network approval boundaries.")
    print("Use it only inside an external container, VM, or equivalent sandbox.")
    if input("Type BYPASS to continue: ").strip() != "BYPASS":
        raise LaunchError("Bypass cancelled.")


def build_codex(preset, permissions, overrides, allow_bypass, do_preflight):
    unsupported = sorted(set(overrides) - set(CODEX_ROLES))
    if unsupported:
        raise LaunchError(
            "Codex has no lead subagent override; root Codex is the conductor-orchestrator. "
            "Unsupported role(s): {}".format(", ".join(unsupported))
        )
    root_model, root_effort = PRESETS[preset]
    agent_files = {}
    for role in CODEX_ROLES:
        selected = overrides.get(role, preset)
        if isinstance(selected, str):
            agent_files[role] = agent_path(selected, role)
        else:
            agent_files[role] = custom_agent_path(role, selected["model"], selected["effort"])
    if do_preflight:
        validate_codex(agent_files, root_model, root_effort)
        validate_codex_mcp()
    command = [
        "codex", "-C", ROOT, "--model", root_model,
        "-c", 'model_reasoning_effort="{}"'.format(root_effort),
    ]
    for role in CODEX_ROLES:
        command.extend(["-c", 'agents.{}.config_file="{}"'.format(role, agent_files[role])])
    if permissions == "safe":
        command.extend(["--sandbox", "workspace-write", "--ask-for-approval", "on-request"])
    else:
        confirm_bypass(allow_bypass)
        command.extend([
            "--dangerously-bypass-approvals-and-sandbox",
            "--dangerously-bypass-hook-trust",
        ])
    return command


def claude_fleet(preset):
    path = os.path.join(CLAUDE_FLEET_DIR, preset + ".json")
    data = read_json(path, None)
    if data is None or not isinstance(data.get("roles"), dict):
        raise LaunchError("Claude fleet manifest missing or invalid: " + path)
    roles = data["roles"]
    missing = [role for role in CLAUDE_ROLES if role not in roles]
    if missing:
        raise LaunchError("Claude fleet {} lacks roles: {}".format(preset, ", ".join(missing)))
    return {role: dict(roles[role]) for role in CLAUDE_ROLES}


def claude_agent_definition(role):
    path = os.path.join(CLAUDE_AGENT_DIR, role + ".md")
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
        raise LaunchError("Claude agent spec missing: " + path)
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.S)
    if not match:
        raise LaunchError("Claude agent spec lacks frontmatter: " + path)
    fields = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() and not line.startswith((" ", "\t")):
            fields[key.strip()] = value.strip()
    return fields, match.group(2).strip()


def validate_claude_fleet(fleet):
    errors = []
    for role in CLAUDE_ROLES:
        spec = fleet[role]
        model, effort = spec.get("model"), spec.get("effort")
        if model not in CLAUDE_MODELS:
            errors.append("{}: model {} is not a Claude model alias".format(role, model))
            continue
        if model == "haiku":
            if effort is not None:
                errors.append("{}: haiku does not accept an effort pin (use null)".format(role))
        elif effort not in CLAUDE_EFFORTS:
            errors.append("{}: invalid effort {}".format(role, effort))
            continue
        if role in ("orchestrator", "orchestrator-opus") and model not in CLAUDE_LEAD_MODELS:
            errors.append("{}: lead model must be fable or opus".format(role))
        if role in CLAUDE_FLOORS:
            floor_model, floor_effort = CLAUDE_FLOORS[role]
            below_model = CLAUDE_MODEL_RANK[model] < CLAUDE_MODEL_RANK[floor_model]
            below_effort = effort is None or CLAUDE_EFFORT_RANK.get(effort, -1) < CLAUDE_EFFORT_RANK[floor_effort]
            if below_model or below_effort:
                errors.append("{}: below the research-gate floor {}@{}".format(role, floor_model, floor_effort))
    if errors:
        raise LaunchError("Invalid Claude fleet:\n  - " + "\n  - ".join(errors))


def claude_quality_drift():
    quality = claude_fleet("quality")
    drifted = []
    for role in CLAUDE_ROLES:
        fields, _ = claude_agent_definition(role)
        pinned = (fields.get("model"), fields.get("effort") or None)
        manifest = (quality[role].get("model"), quality[role].get("effort") or None)
        if pinned != manifest:
            drifted.append(role)
    if drifted:
        raise LaunchError(
            "quality manifest out of sync with .claude/agents frontmatter: " + ", ".join(drifted))


def resolve_claude_fleet(preset, overrides):
    fleet = claude_fleet(preset)
    for role, selected in overrides.items():
        if isinstance(selected, str):
            fleet[role] = claude_fleet(selected)[role]
            continue
        model, effort = selected["model"], selected["effort"]
        if model == "haiku":
            raise LaunchError(
                "{}: haiku does not accept an effort pin; borrow a preset row instead "
                "(e.g. --role {}=fast)".format(role, role))
        if model not in CLAUDE_MODELS or effort not in CLAUDE_EFFORTS:
            raise LaunchError(
                "--role {}={}@{} is not a valid Claude override (models: {}; efforts: {})".format(
                    role, model, effort,
                    "/".join(sorted(CLAUDE_MODELS)), "/".join(sorted(CLAUDE_EFFORTS))))
        fleet[role] = {"model": model, "effort": effort}
    validate_claude_fleet(fleet)
    return fleet


def claude_agents_overlay(changed, fleet):
    overlay = {}
    for role in changed:
        fields, body = claude_agent_definition(role)
        entry = {"description": fields.get("description", ""), "prompt": body,
                 "model": fleet[role]["model"]}
        if fleet[role].get("effort"):
            entry["effort"] = fleet[role]["effort"]
        for key in ("tools", "skills"):
            if fields.get(key):
                entry[key] = [item.strip() for item in fields[key].split(",") if item.strip()]
        if fields.get("memory"):
            entry["memory"] = fields["memory"]
        overlay[role] = entry
    return overlay


def build_claude(preset, permissions, overrides, allow_bypass, do_preflight):
    unsupported = sorted(set(overrides) - set(CLAUDE_CORE_ROLES))
    if unsupported:
        raise LaunchError("Unsupported Claude role override(s): {}".format(", ".join(unsupported)))
    if do_preflight and not shutil.which("claude"):
        raise LaunchError("Claude CLI is not installed or not on PATH.")
    command = ["claude"]
    if preset != "quality" or overrides:
        fleet = resolve_claude_fleet(preset, overrides)
        claude_quality_drift()
        quality = claude_fleet("quality")
        changed = [role for role in CLAUDE_ROLES if fleet[role] != quality[role]]
        if fleet["orchestrator"] != quality["orchestrator"]:
            command.extend(["--model", fleet["orchestrator"]["model"],
                            "--effort", fleet["orchestrator"]["effort"]])
        if changed:
            overlay = claude_agents_overlay(changed, fleet)
            command.extend(["--agents", json.dumps(overlay, ensure_ascii=False)])
    if permissions == "bypass":
        confirm_bypass(allow_bypass)
        command.append("--dangerously-skip-permissions")
    return command


def save_config(config):
    os.makedirs(os.path.dirname(LOCAL_CONFIG), exist_ok=True)
    with open(LOCAL_CONFIG, "w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2, sort_keys=True)
        handle.write("\n")


def enforce_backend_lock(saved, selected):
    """Warn (not refuse) when launching the non-default backend from this checkout.

    Provider research state is already isolated per plane (.claude/ vs .codex/), so a
    cross-backend launch is a supported explicit choice; the warning exists because the
    research-code surfaces (models/, evaluation/, data/, run.sh) are shared between
    planes. Bare `./orchestrate` still launches the saved default; change the default
    with `./orchestrate --configure`."""
    locked = saved.get("backend")
    if locked and locked != selected:
        print(
            "orchestrate: note — this checkout's default backend is '{}'; launching '{}'.\n"
            "  Research state stays per-provider, but models/, evaluation/, data/, and the\n"
            "  run entry points are shared: avoid concurrent provider runs on the same files.\n"
            "  Change the default with './orchestrate --configure'.".format(locked, selected),
            file=sys.stderr,
        )


def parser():
    result = argparse.ArgumentParser(
        description="Initialize, diagnose, audit, or launch an isolated research orchestrator."
    )
    result.add_argument(
        "command", nargs="?",
        choices=("codex", "claude", "init", "doctor", "demo", "release-check", "audit", "runs"),
    )
    result.add_argument(
        "target", nargs="?",
        help="backend for init/doctor, audit run id/latest, or 'list' for runs",
    )
    result.add_argument("--preset", choices=tuple(PRESETS), help="fleet preset")
    result.add_argument("--permissions", choices=("safe", "bypass"))
    result.add_argument("--backend", choices=("codex", "claude"), help="backend for audit commands")
    result.add_argument("--json", action="store_true", help="machine-readable audit output")
    result.add_argument("--role", action="append", default=[], metavar="ROLE=PRESET|MODEL@EFFORT")
    result.add_argument("--configure", action="store_true", help="choose and save defaults")
    result.add_argument("--dry-run", action="store_true", help="print the command without launching")
    result.add_argument("--allow-unsafe-bypass", action="store_true")
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    if args.command not in ("init", "doctor", "audit", "runs") and args.target is not None:
        raise LaunchError("unexpected positional argument: {}".format(args.target))
    if args.command not in ("audit", "runs") and (args.backend or args.json):
        raise LaunchError("--backend and --json are audit-command options")
    saved = read_json(LOCAL_CONFIG, {})
    if args.command == "init":
        backend = args.target or saved.get("backend")
        if not backend:
            backend = choose("Select one backend for this checkout:", ["codex", "claude"], "codex")
        if backend not in ("codex", "claude"):
            raise LaunchError("init backend must be codex or claude")
        enforce_backend_lock(saved, backend)
        should_bind = not saved.get("backend")
        result = initialize_project(backend)
        if should_bind:
            saved.update({
                "backend": backend, "preset": "quality", "permissions": "safe",
                "role_overrides": {},
            })
            save_config(saved)
        return result
    if args.command == "doctor":
        backend = args.target or saved.get("backend")
        if not backend:
            backend = choose("Select backend to diagnose:", ["codex", "claude"], "codex")
        if backend not in ("codex", "claude"):
            raise LaunchError("doctor backend must be codex or claude")
        enforce_backend_lock(saved, backend)
        return doctor(backend)
    if args.command == "demo":
        return run_demo()
    if args.command == "release-check":
        return release_check()
    if args.command in ("audit", "runs"):
        backend = args.backend or saved.get("backend") or "codex"
        if backend != "codex":
            raise LaunchError(
                "Native durable audit is currently Codex-only; the Claude control plane does not "
                "read or write the Codex run store."
            )
        if args.command == "audit":
            command = ["audit", args.target or "latest"]
        else:
            if args.target not in (None, "list"):
                raise LaunchError("runs accepts only 'list'")
            command = ["list"]
        if args.json:
            command.append("--json")
        return codex_audit(command).returncode
    if args.configure:
        selected_backend = choose(
            "Select orchestration backend:", ["codex", "claude"], saved.get("backend", "codex"))
        enforce_backend_lock(saved, selected_backend)
        saved = {
            "backend": selected_backend,
            "permissions": choose("Select permission posture:", ["safe", "bypass"], saved.get("permissions", "safe")),
            "preset": choose("Select fleet preset:", ["quality", "balanced", "fast"], saved.get("preset", "quality")),
            "role_overrides": saved.get("role_overrides", {}),
        }
        save_config(saved)
        print("Saved " + LOCAL_CONFIG)
        if args.command is None:
            return 0
    backend = args.command or saved.get("backend")
    if not backend:
        backend = choose("Select orchestration backend:", ["codex", "claude"], "codex")
    enforce_backend_lock(saved, backend)
    preset = args.preset or saved.get("preset", "quality")
    permissions = args.permissions or saved.get("permissions", "safe")
    overrides = dict(saved.get("role_overrides", {}))
    for text in args.role:
        role, value = parse_override(text)
        overrides[role] = value
    if backend == "codex":
        command = build_codex(preset, permissions, overrides, args.allow_unsafe_bypass, not args.dry_run)
    else:
        command = build_claude(preset, permissions, overrides, args.allow_unsafe_bypass, not args.dry_run)
    if args.dry_run:
        print(shlex.join(command))
        return 0
    if not saved.get("backend"):
        saved.update({"backend": backend, "preset": preset, "permissions": permissions,
                      "role_overrides": overrides})
        save_config(saved)
    audit_run = start_codex_audit(preset, permissions) if backend == "codex" else None
    identity = " run={}".format(audit_run["run_id"]) if audit_run else ""
    topology = "root-conductor-direct" if backend == "codex" else "adaptive-direct"
    print(
        "[orchestrate] backend={} fleet={} permissions={} topology={}{}".format(
            backend, preset, permissions, topology, identity
        ), flush=True,
    )
    os.chdir(ROOT)
    os.execvpe(command[0], command, load_backend_env(
        backend, preset, permissions, audit_run=audit_run
    ))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LaunchError as exc:
        print("orchestrate: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
