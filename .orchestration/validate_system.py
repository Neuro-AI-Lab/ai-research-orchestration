#!/usr/bin/env python3
"""Deterministic release validation for the dual-backend distribution."""

import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

try:
    import tomllib
except ImportError:  # Python 3.8-3.10 validation falls back to Codex parsing.
    tomllib = None


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODEX_ROLES = (
    "brainstorm", "data", "critic", "developer", "qa", "experiment-tracker",
    "filemanager", "writer",
)
CODEX_SKILLS = (
    "codex-multiagent-orchestration", "codex-specialist-core", "data-leakage-audit",
    "experiment-analysis", "experiment-reproducibility", "grounded-research-writing",
    "hypothesis-design", "literature-evidence-review", "research-paper-workflow",
    "research-validity-review", "version-management",
)
CLAUDE_SKILLS = (
    "data-leakage-audit", "experiment-reproducibility", "grounded-research-writing",
    "hypothesis-design", "multiagent-orchestration", "research-validity-review",
    "specialist-core", "version-management",
)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


launcher = load_module("orchestration_launcher", os.path.join(ROOT, ".orchestration", "launcher.py"))
result_gate = load_module("result_contract_gate", os.path.join(ROOT, ".codex", "hooks", "result_contract_gate.py"))
claude_result_gate = load_module(
    "claude_result_contract_gate",
    os.path.join(ROOT, ".claude", "hooks", "result_contract_gate.py"))


class DistributionValidation(unittest.TestCase):
    def test_required_files_and_fleets(self):
        for path in ("README.md", "README.ko.md", "AGENTS.md", "CLAUDE.md",
                     "docs/orchestration/CODEX.md", "docs/orchestration/CODEX.ko.md",
                     "docs/orchestration/CLAUDE.md", "docs/orchestration/CLAUDE.ko.md",
                     "docs/orchestration/MAINTAINERS.md",
                     "docs/orchestration/MAINTAINERS.ko.md",
                     "docs/orchestration/PROJECT_MAP.md",
                     "docs/orchestration/PROJECT_MAP.ko.md", ".codex/ORCHESTRATION.md",
                     ".codex/templates/plan/PRD.md",
                     ".codex/templates/plan/CHECKLIST.md",
                     ".codex/templates/report/discussion.md",
                     ".codex/templates/report/issue.md",
                     ".codex/templates/report/result.md",
                     ".codex/templates/report/version.md",
                     ".claude/templates/plan/PRD.md",
                     ".claude/templates/plan/CHECKLIST.md",
                     ".claude/templates/report/discussion.md",
                     ".claude/templates/report/issue.md",
                     ".claude/templates/report/result.md",
                     ".claude/templates/report/version.md",
                     "plan/PRD.md", "plan/CHECKLIST.md",
                     "report/discussion.md", "report/issue.md",
                     "report/result.md", "report/version.md",
                     "requirements.txt", ".codex/config.toml",
                     ".codex/hooks/audit_event.py", ".codex/scripts/orchestration_audit.py",
                     ".orchestration/release_check.py", ".orchestration/isolation.py",
                     ".orchestration/project_map.json", ".orchestration/validate_system.py",
                     "orchestrate"):
            self.assertTrue(os.path.isfile(os.path.join(ROOT, path)), path)
        for path in ("SETUP.md", "SETUP.ko.md", "SECURITY.md", "SECURITY.ko.md",
                     "CONTRIBUTING.md", ".codex/README.md", ".claude/README.md"):
            self.assertFalse(os.path.exists(os.path.join(ROOT, path)), path)
        for preset in ("quality", "balanced", "fast"):
            for role in CODEX_ROLES:
                self.assertTrue(os.path.isfile(launcher.agent_path(preset, role)))
                self.assertTrue(os.path.isfile(os.path.join(ROOT, ".codex", "prompts", "roles", role + ".md")))

    def test_agent_git_mutations_require_explicit_user_authority(self):
        policies = {
            "AGENTS.md": ("explicit user", "stage", "branch", "commit", "pull", "push", "pull request", "merge"),
            ".codex/ORCHESTRATION.md": (
                "explicit user", "stage", "branch", "commit", "pull", "push", "pull request", "merge",
            ),
            ".agents/skills/codex-specialist-core/SKILL.md": (
                "user's explicit request", "stage", "branch", "commit", "pull", "push", "pull request", "merge",
            ),
            "CLAUDE.md": ("explicit user", "stage", "branch", "commit", "pull", "push", "pull request", "merge"),
            ".claude/skills/specialist-core/SKILL.md": (
                "user's explicit request", "stage", "branch", "commit", "pull", "push", "pull request", "merge",
            ),
        }
        for path, required in policies.items():
            with self.subTest(path=path):
                with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
                    content = handle.read().lower()
                for token in required:
                    self.assertIn(token, content)

    def test_project_map_matches_canonical_workspace(self):
        with open(os.path.join(ROOT, ".orchestration", "project_map.json"),
                  encoding="utf-8") as handle:
            project_map = json.load(handle)
        expected = {
            "plan/", "report/", "data/", "model/", "experiments/", "analysis/",
            "functionals/", "utils/",
        }
        actual = set(project_map["categories"]["research-workspace"]["paths"])
        self.assertTrue(expected.issubset(actual))
        self.assertIn("run.sh", actual)
        self.assertIn("evaluate.sh", actual)
        self.assertIn("README.md", project_map["categories"]["adapt-and-rewrite"]["files"])
        providers = project_map["categories"]["provider-orchestration-core"]["providers"]
        self.assertEqual(set(providers), {"codex", "claude"})
        self.assertIn(".codex/", providers["codex"]["paths"])
        self.assertIn(".claude/", providers["claude"]["paths"])

    def test_adaptation_report_is_provider_aware_and_read_only(self):
        report = launcher.adaptation_report("codex")
        self.assertEqual(report["backend"], "codex")
        self.assertEqual(report["unselected_provider"], "claude")
        self.assertIn(".claude/", report["unselected_provider_paths"])
        self.assertIn("docs/", report["template_only_paths"])
        self.assertIn("requirements.txt", {item["path"] for item in report["rewrite_files"]})
        self.assertFalse(report["mutated"])
        parsed = launcher.parser().parse_args(["adapt", "codex", "--json"])
        self.assertEqual((parsed.command, parsed.target, parsed.json), ("adapt", "codex", True))

    def test_codex_skill_set_is_complete_and_distribution_ready(self):
        skill_root = os.path.join(ROOT, ".agents", "skills")
        discovered = sorted(
            name for name in os.listdir(skill_root)
            if os.path.isfile(os.path.join(skill_root, name, "SKILL.md"))
        )
        self.assertEqual(discovered, sorted(CODEX_SKILLS))
        for name in CODEX_SKILLS:
            path = os.path.join(skill_root, name, "SKILL.md")
            with open(path, encoding="utf-8") as handle:
                content = handle.read()
            self.assertRegex(content, r"(?m)^---\nname: " + re.escape(name) + r"\n")
            self.assertRegex(content, r"(?m)^description: (?:[^\n]+|>-)$")
            frontmatter = content.split("---", 2)[1]
            self.assertEqual(
                re.findall(r"(?m)^([a-z][a-z0-9_-]*):", frontmatter),
                ["name", "description"],
            )
            self.assertNotRegex(content, r"(?i)\b(?:TODO|TBD|FIXME)\b")
            self.assertNotIn(".claude/", content)

    def test_claude_skill_set_is_complete_and_distribution_ready(self):
        skill_root = os.path.join(ROOT, ".claude", "skills")
        discovered = sorted(
            name for name in os.listdir(skill_root)
            if os.path.isfile(os.path.join(skill_root, name, "SKILL.md"))
        )
        self.assertEqual(discovered, sorted(CLAUDE_SKILLS))
        for name in CLAUDE_SKILLS:
            path = os.path.join(skill_root, name, "SKILL.md")
            with open(path, encoding="utf-8") as handle:
                content = handle.read()
            self.assertRegex(content, r"(?m)^---\nname: " + re.escape(name) + r"\n")
            self.assertRegex(content, r"(?m)^description: (?:[^\n]+|>-?|>)$")
            frontmatter = content.split("---", 2)[1]
            self.assertEqual(
                re.findall(r"(?m)^([a-z][a-z0-9_-]*):", frontmatter),
                ["name", "description"],
            )
            self.assertNotRegex(content, r"(?i)\b(?:TODO|TBD|FIXME)\b")
            self.assertNotIn(".codex/", content)

    def test_toml_parses(self):
        if tomllib is None:
            self.skipTest("tomllib unavailable on this Python; Codex prompt-input validates config")
        paths = [os.path.join(ROOT, ".codex", "config.toml")]
        paths.extend(launcher.agent_path(preset, role)
                     for preset in launcher.PRESETS for role in CODEX_ROLES)
        for path in paths:
            with open(path, "rb") as handle:
                tomllib.load(handle)

    def test_codex_mcp_config_and_stdio_tool_discovery(self):
        if tomllib is None:
            self.skipTest("tomllib unavailable")
        with open(os.path.join(ROOT, ".codex", "config.toml"), "rb") as handle:
            config = tomllib.load(handle)
        requests = "\n".join((
            json.dumps({
                "jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "distribution-validator", "version": "1"},
                },
            }),
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
        )) + "\n"
        self.assertEqual(set(config["mcp_servers"]), set(launcher.CODEX_MCP_SERVERS))
        for name, expected in launcher.CODEX_MCP_SERVERS.items():
            registered = config["mcp_servers"][name]
            self.assertEqual(registered["command"], expected["command"])
            self.assertEqual(registered["args"], expected["args"])
            self.assertTrue(all(part.startswith(".codex/") for part in expected["args"][:1]))
            proc = subprocess.run(
                [sys.executable] + expected["args"], cwd=ROOT, input=requests,
                text=True, capture_output=True, timeout=10, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            responses = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
            listing = next(item for item in responses if item.get("id") == 2)
            tools = {item["name"] for item in listing["result"]["tools"]}
            self.assertEqual(tools, expected["tools"])

    def test_codex_native_audit_hooks_are_wired(self):
        if tomllib is None:
            self.skipTest("tomllib unavailable")
        with open(os.path.join(ROOT, ".codex", "config.toml"), "rb") as handle:
            config = tomllib.load(handle)
        for event in ("SessionStart", "SubagentStart", "SubagentStop"):
            commands = [
                hook["command"]
                for group in config["hooks"][event]
                for hook in group.get("hooks", [])
            ]
            self.assertTrue(any("audit_event.py" in command for command in commands), event)
        with open(os.path.join(ROOT, ".codex", "hooks", "session_close_gate.py"),
                  encoding="utf-8") as handle:
            close_hook = handle.read()
        self.assertIn("record_turn_stop", close_hook)
        self.assertIn("turn_stopped", close_hook)

    def test_clean_root_templates_match_positive_gate_schema(self):
        template_dir = os.path.join(ROOT, ".codex", "templates", "report")
        with open(os.path.join(template_dir, "discussion.md"), encoding="utf-8") as handle:
            discussion = handle.read()
        self.assertIn("## [REV-NNN]", discussion)
        self.assertIn("## [QA-NNN]", discussion)
        self.assertIn("**Gate:** passed | blocked", discussion)
        self.assertIn("**Leakage audit:** passed | blocked", discussion)
        for name in ("discussion.md", "result.md", "issue.md", "version.md"):
            with open(os.path.join(template_dir, name), encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("## Summary", content)
        for backend in ("codex", "claude"):
            provider = os.path.join(ROOT, "." + backend)
            for name in ("discussion.md", "result.md", "issue.md", "version.md"):
                self.assertTrue(os.path.isfile(os.path.join(provider, "templates", "report", name)))
            for name in ("PRD.md", "CHECKLIST.md"):
                self.assertTrue(os.path.isfile(os.path.join(provider, "templates", "plan", name)))
        for name in ("discussion.md", "result.md", "issue.md", "version.md"):
            with open(os.path.join(ROOT, "report", name), encoding="utf-8") as handle:
                self.assertIn("## Summary", handle.read())
        for role in ("conductor", "brainstorm", "critic"):
            self.assertTrue(os.path.isfile(os.path.join(
                ROOT, ".codex", "templates", "memory", role, "MEMORY.md"
            )))
        for role in ("orchestrator", "brainstorm", "critic"):
            self.assertTrue(os.path.isfile(os.path.join(
                ROOT, ".claude", "templates", "memory", role, "MEMORY.md"
            )))

    def test_role_overrides(self):
        self.assertEqual(launcher.parse_override("brainstorm=fast"), ("brainstorm", "fast"))
        role, value = launcher.parse_override("critic=gpt-5.6-sol@max")
        self.assertEqual(role, "critic")
        self.assertEqual(value, {"model": "gpt-5.6-sol", "effort": "max"})
        with self.assertRaises(launcher.LaunchError):
            launcher.parse_override("unknown=fast")

    def test_checkout_backend_lock_refuses_cross_launch(self):
        launcher.enforce_backend_lock({}, "codex")
        launcher.enforce_backend_lock({"backend": "codex"}, "codex")
        with self.assertRaises(launcher.LaunchError) as raised:
            launcher.enforce_backend_lock({"backend": "codex"}, "claude")
        self.assertIn("separate clone/worktree", str(raised.exception))

    def test_initialization_creates_only_the_selected_provider_state(self):
        original_root = launcher.ROOT
        with tempfile.TemporaryDirectory() as root:
            try:
                launcher.ROOT = root
                sources = [
                    ".codex/settings.local.json.example",
                    ".codex/state/handoff.json.example",
                ]
                sources.extend(
                    ".codex/templates/report/{}".format(name)
                    for name in ("discussion.md", "result.md", "issue.md", "version.md")
                )
                sources.extend((
                    ".codex/templates/plan/PRD.md",
                    ".codex/templates/plan/CHECKLIST.md",
                ))
                sources.extend(
                    ".codex/templates/memory/{}/MEMORY.md".format(role)
                    for role in ("conductor", "brainstorm", "critic")
                )
                for relative in sources:
                    path = os.path.join(root, relative)
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "w", encoding="utf-8") as handle:
                        handle.write("{}\n" if path.endswith(".json.example") else "# clean seed\n")
                with contextlib.redirect_stdout(io.StringIO()):
                    launcher.initialize_project("codex")
                self.assertTrue(os.path.isfile(os.path.join(
                    root, ".codex", "memory", "conductor", "MEMORY.md"
                )))
                self.assertTrue(os.path.isfile(os.path.join(
                    root, ".codex", "state", "handoff.json"
                )))
                self.assertFalse(os.path.exists(os.path.join(root, ".claude")))
                for relative in (
                    "plan/PRD.md", "plan/CHECKLIST.md", "report/discussion.md",
                    "report/result.md", "report/issue.md", "report/version.md", "data",
                    "model", "experiments/runs", "analysis", "functionals", "utils",
                ):
                    self.assertTrue(os.path.exists(os.path.join(root, relative)), relative)
            finally:
                launcher.ROOT = original_root

    def test_claude_initialization_creates_its_workspace_only(self):
        original_root = launcher.ROOT
        with tempfile.TemporaryDirectory() as root:
            try:
                launcher.ROOT = root
                sources = [
                    ".claude/settings.local.json.example",
                    ".claude/state/handoff.json.example",
                ]
                sources.extend(
                    ".claude/templates/report/{}".format(name)
                    for name in ("discussion.md", "result.md", "issue.md", "version.md")
                )
                sources.extend(
                    ".claude/templates/memory/{}/MEMORY.md".format(role)
                    for role in ("orchestrator", "brainstorm", "critic")
                )
                sources.extend((
                    ".claude/templates/plan/PRD.md",
                    ".claude/templates/plan/CHECKLIST.md",
                ))
                for relative in sources:
                    path = os.path.join(root, relative)
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "w", encoding="utf-8") as handle:
                        handle.write("{}\n" if path.endswith(".json.example") else "# clean seed\n")
                with contextlib.redirect_stdout(io.StringIO()):
                    launcher.initialize_project("claude")
                for relative in (
                    "plan/PRD.md", "plan/CHECKLIST.md", "report/discussion.md",
                    "report/result.md", "report/issue.md", "report/version.md", "data",
                    "model", "experiments/runs", "analysis", "functionals", "utils",
                ):
                    self.assertTrue(os.path.exists(os.path.join(root, relative)), relative)
                self.assertFalse(os.path.exists(os.path.join(root, ".codex")))
                self.assertFalse(os.path.exists(os.path.join(root, "experiments", "codex")))
            finally:
                launcher.ROOT = original_root

    def test_runtime_environment_loads_only_selected_provider_settings(self):
        original_root = launcher.ROOT
        with tempfile.TemporaryDirectory() as root:
            try:
                launcher.ROOT = root
                for backend, key in (("codex", "CODEX_FIXTURE"), ("claude", "CLAUDE_FIXTURE")):
                    directory = os.path.join(root, "." + backend)
                    os.makedirs(directory)
                    with open(os.path.join(directory, "settings.local.json"),
                              "w", encoding="utf-8") as handle:
                        json.dump({"env": {key: "selected"}}, handle)
                codex_env = launcher.load_backend_env("codex")
                self.assertEqual(codex_env["CODEX_FIXTURE"], "selected")
                self.assertNotIn("CLAUDE_FIXTURE", codex_env)
                claude_env = launcher.load_backend_env("claude")
                self.assertEqual(claude_env["CLAUDE_FIXTURE"], "selected")
                self.assertNotIn("CODEX_FIXTURE", claude_env)
            finally:
                launcher.ROOT = original_root

    def test_audit_cli_and_environment_contract(self):
        args = launcher.parser().parse_args(["audit", "latest", "--json"])
        self.assertEqual((args.command, args.target, args.json), ("audit", "latest", True))
        args = launcher.parser().parse_args(["runs", "list"])
        self.assertEqual((args.command, args.target), ("runs", "list"))
        env = launcher.load_backend_env(
            "codex", "quality", "safe",
            audit_run={"run_id": "ORCH-00000000-001", "run_dir": "/tmp/run"},
        )
        self.assertEqual(env["ORCHESTRATION_RUN_ID"], "ORCH-00000000-001")
        self.assertEqual(env["ORCHESTRATION_RUN_DIR"], "/tmp/run")
        self.assertEqual(env["ORCHESTRATION_TOPOLOGY"], "root-conductor-direct")
        claude_env = launcher.load_backend_env("claude", "quality", "safe")
        self.assertEqual(claude_env["ORCHESTRATION_TOPOLOGY"], "adaptive-direct")

    def test_custom_role_cache_is_deterministic_and_not_created_for_presets(self):
        original = launcher.CACHE_DIR
        with tempfile.TemporaryDirectory() as root:
            launcher.CACHE_DIR = os.path.join(root, "cache")
            try:
                launcher.build_codex("quality", "safe", {}, False, False)
                self.assertFalse(os.path.exists(launcher.CACHE_DIR))
                overrides = {"developer": {"model": "gpt-5.6-terra", "effort": "high"}}
                first = launcher.build_codex("quality", "safe", overrides, False, False)
                second = launcher.build_codex("quality", "safe", overrides, False, False)
                cached_args = [part for part in first if "developer-" in part and ".toml" in part]
                cached = [re.search(r'config_file="([^"]+)', part).group(1) for part in cached_args]
                self.assertEqual(len(cached), 1)
                self.assertTrue(any(cached[0] in part for part in second))
                self.assertTrue(os.path.isfile(cached[0]))
            finally:
                launcher.CACHE_DIR = original

    def test_dry_run_commands(self):
        codex = launcher.build_codex("quality", "safe", {}, False, False)
        self.assertIn("--strict-config", codex)
        self.assertEqual(codex[codex.index("--model") + 1], "gpt-5.6-luna")
        self.assertIn("features.multi_agent_v2=false", codex)
        self.assertIn("--sandbox", codex)
        self.assertIn("workspace-write", codex)
        self.assertIn("on-request", codex)
        self.assertFalse(any("agents.orchestrator.config_file" in part for part in codex))
        self.assertEqual(
            sum("agents." in part and ".config_file=" in part for part in codex),
            len(CODEX_ROLES),
        )
        with self.assertRaises(launcher.LaunchError):
            launcher.build_codex("quality", "safe", {"orchestrator": "quality"}, False, False)
        self.assertEqual(launcher.build_claude("quality", "safe", {}, False, False), ["claude"])
        bypass = launcher.build_codex("quality", "bypass", {}, True, False)
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", bypass)
        self.assertIn("--dangerously-bypass-hook-trust", bypass)

    def test_result_contract_validation(self):
        self.assertIsNotNone(result_gate.validation_error("done"))
        missing_evidence = """## RESULT
**Status:** complete
**Deliverables:** x
**Evidence:** none
**Open items:** none
**Next:** none
"""
        self.assertIn("evidence", result_gate.validation_error(missing_evidence).lower())
        valid = missing_evidence.replace("**Evidence:** none", "**Evidence:**\n- ✅ `pytest` passed")
        self.assertIsNone(result_gate.validation_error(valid))

    def test_claude_fleet_manifests_and_quality_drift(self):
        for preset in ("quality", "balanced", "fast"):
            fleet = launcher.claude_fleet(preset)
            self.assertEqual(set(fleet), set(launcher.CLAUDE_ROLES))
            launcher.validate_claude_fleet(fleet)
        launcher.claude_quality_drift()

    def test_claude_fleet_dry_run_commands(self):
        self.assertEqual(launcher.build_claude("quality", "safe", {}, False, False), ["claude"])
        balanced = launcher.build_claude("balanced", "safe", {}, False, False)
        self.assertNotIn("--model", balanced)
        overlay = json.loads(balanced[balanced.index("--agents") + 1])
        self.assertEqual(overlay["critic"]["effort"], "xhigh")
        self.assertEqual(overlay["critic"]["model"], "sonnet")
        self.assertIn("research-validity-review", overlay["critic"]["skills"])
        self.assertNotIn("orchestrator", overlay)
        fast = launcher.build_claude("fast", "safe", {}, False, False)
        self.assertEqual(fast[fast.index("--model") + 1], "fable")
        self.assertEqual(fast[fast.index("--effort") + 1], "high")
        overlay = json.loads(fast[fast.index("--agents") + 1])
        self.assertEqual(overlay["experiment-tracker"]["model"], "haiku")
        self.assertNotIn("effort", overlay["experiment-tracker"])
        self.assertEqual(overlay["orchestrator"]["model"], "fable")
        self.assertEqual(overlay["orchestrator"]["effort"], "high")
        borrowed = launcher.build_claude("fast", "safe", {"critic": "quality"}, False, False)
        overlay = json.loads(borrowed[borrowed.index("--agents") + 1])
        self.assertEqual(overlay.get("critic", {}).get("effort", "max"), "max")

    def test_claude_fleet_floors_and_invalid_overrides(self):
        with self.assertRaises(launcher.LaunchError):
            launcher.build_claude(
                "quality", "safe", {"critic": {"model": "sonnet", "effort": "medium"}}, False, False)
        with self.assertRaises(launcher.LaunchError):
            launcher.build_claude(
                "quality", "safe", {"qa": {"model": "haiku", "effort": "low"}}, False, False)
        with self.assertRaises(launcher.LaunchError):
            launcher.build_claude(
                "quality", "safe", {"developer": {"model": "gpt-5.6-sol", "effort": "max"}},
                False, False)
        with self.assertRaises(launcher.LaunchError):
            launcher.build_claude(
                "quality", "safe", {"developer": {"model": "sonnet", "effort": "ultra"}},
                False, False)

    def test_result_contract_gates_have_independent_paths_and_same_acceptance(self):
        cases = (
            "done",
            "## RESULT\n**Status:** complete\n**Deliverables:** x\n"
            "**Evidence:** none\n**Open items:** none\n**Next:** none\n",
            "## RESULT\n**Status:** complete\n**Deliverables:** x\n"
            "**Evidence:**\n- ✅ `pytest` passed\n**Open items:** none\n**Next:** none\n",
            "## RESULT\n**Status:** blocked\n**Deliverables:** none\n"
            "**Evidence:**\n- ❌ dataset missing\n**Open items:** which split?\n**Next:** none\n",
        )
        for message in cases:
            self.assertEqual(claude_result_gate.validation_error(message) is None,
                             result_gate.validation_error(message) is None, message)
        self.assertIn(".claude/", claude_result_gate.validation_error("done"))
        self.assertIn(".codex/", result_gate.validation_error("done"))

    def test_claude_result_contract_gate_hook_behavior(self):
        hook = os.path.join(ROOT, ".claude", "hooks", "result_contract_gate.py")
        def invoke(payload):
            proc = subprocess.run([sys.executable, hook], input=json.dumps(payload),
                                  text=True, capture_output=True, cwd=ROOT)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            return proc.stdout.strip()
        blocked = invoke({"agent_type": "critic", "stop_hook_active": False,
                          "last_assistant_message": "review finished"})
        self.assertIn('"decision": "block"', blocked)
        self.assertEqual(invoke({"agent_type": "orchestrator", "stop_hook_active": False,
                                 "last_assistant_message": "no result block"}), "")
        self.assertEqual(invoke({"agent_type": "", "stop_hook_active": False,
                                 "last_assistant_message": "no result block"}), "")
        self.assertEqual(invoke({"agent_type": "critic", "stop_hook_active": True,
                                 "last_assistant_message": "still no result block"}), "")
        compliant = ("## RESULT\n**Status:** complete\n**Deliverables:** REV-001\n"
                     "**Evidence:**\n- ✅ read discussion.md entry\n"
                     "**Open items:** none\n**Next:** none\n")
        self.assertEqual(invoke({"agent_type": "critic", "stop_hook_active": False,
                                 "last_assistant_message": compliant}), "")

    def test_claude_settings_wire_subagent_stop_gate(self):
        with open(os.path.join(ROOT, ".claude", "settings.json"), encoding="utf-8") as handle:
            settings = json.load(handle)
        commands = [hook["command"]
                    for entry in settings["hooks"].get("SubagentStop", [])
                    for hook in entry["hooks"]]
        self.assertTrue(any("result_contract_gate.py" in command for command in commands))

    def test_codex_experiment_gate_is_native(self):
        hook = os.path.join(ROOT, ".codex", "hooks", "experiment_gate.py")
        mention = {"tool_name": "Bash", "tool_input": {"command": "rg 'run.sh' README.md"}}
        proc = subprocess.run([sys.executable, hook],
                              input=json.dumps(mention), text=True, capture_output=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        launch = {"tool_name": "Bash", "tool_input": {"command": "./run.sh train"}}
        proc = subprocess.run([sys.executable, hook],
                              input=json.dumps(launch), text=True, capture_output=True, cwd=ROOT)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("GATE", proc.stderr)

    def test_codex_run_status_wrapper_matches_single_and_sweep_layouts(self):
        wrapper = os.path.join(ROOT, ".codex", "scripts", "run_with_status.sh")
        with tempfile.TemporaryDirectory() as root:
            env = dict(os.environ, EXPERIMENTS_DIR=os.path.join(root, "runs"))
            single = subprocess.run(
                [wrapper, "EXP-001", "--", "true"], text=True, capture_output=True, env=env,
                check=False,
            )
            self.assertEqual(single.returncode, 0, single.stderr)
            with open(os.path.join(root, "runs", "EXP-001", "status.json"),
                      encoding="utf-8") as handle:
                self.assertEqual(json.load(handle)["state"], "completed")
            tagged = subprocess.run(
                [wrapper, "EXP-002", "--tag", "seed-1", "--", "true"],
                text=True, capture_output=True, env=env, check=False,
            )
            self.assertEqual(tagged.returncode, 0, tagged.stderr)
            tagged_status = os.path.join(
                root, "runs", "EXP-002", "runs", "seed-1", "status.json"
            )
            with open(tagged_status, encoding="utf-8") as handle:
                status = json.load(handle)
            self.assertEqual((status["exp_id"], status["run_tag"], status["state"]),
                             ("EXP-002", "seed-1", "completed"))
            invalid = subprocess.run(
                [wrapper, "../escape", "--", "true"], text=True, capture_output=True, env=env,
                check=False,
            )
            self.assertEqual(invalid.returncode, 64)

    def test_positive_research_gate_attestations(self):
        hook = os.path.join(ROOT, ".claude", "hooks", "experiment_gate.py")
        launch = json.dumps({"tool_name": "Bash", "tool_input": {"command": "./run.sh train"}})
        discussion = """# discussion
## [DATASET-001] synthetic fixture | data
**Leakage audit:** passed
## [REV-001] synthetic plan review | critic
**Severity:** major
**Gate:** passed
**Status:** resolved
## [QA-001] synthetic code verification | qa
**Gate:** passed
**Status:** complete
"""
        with tempfile.TemporaryDirectory() as root:
            state = os.path.join(root, "report")
            os.makedirs(state)
            with open(os.path.join(state, "discussion.md"), "w", encoding="utf-8") as handle:
                handle.write(discussion)
            with open(os.path.join(state, "issue.md"), "w", encoding="utf-8") as handle:
                handle.write("# issue\n")
            env = dict(os.environ, CLAUDE_PROJECT_DIR=root)
            proc = subprocess.run([sys.executable, hook], input=launch,
                                  text=True, capture_output=True, cwd=ROOT, env=env)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            with open(os.path.join(state, "discussion.md"), "w", encoding="utf-8") as handle:
                handle.write(discussion.replace("**Gate:** passed\n**Status:** complete", "**Gate:** blocked\n**Status:** blocked"))
            proc = subprocess.run([sys.executable, hook], input=launch,
                                  text=True, capture_output=True, cwd=ROOT, env=env)
            self.assertEqual(proc.returncode, 2)
            self.assertIn("QA entry", proc.stderr)
            incomplete_adr = """# discussion
## [ADR-001] synthetic incomplete override | orchestrator
**Context:** test
**Decision:** bypass
**Consequences:** test only
"""
            with open(os.path.join(state, "discussion.md"), "w", encoding="utf-8") as handle:
                handle.write(incomplete_adr)
            override = json.dumps({"tool_name": "Bash", "tool_input": {
                "command": "GATE_OVERRIDE=ADR-001 ./run.sh train"}})
            proc = subprocess.run([sys.executable, hook], input=override,
                                  text=True, capture_output=True, cwd=ROOT, env=env)
            self.assertEqual(proc.returncode, 2)
            self.assertIn("Rollback", proc.stderr)

    def test_shell_heredoc_launch_is_gated_but_data_heredoc_is_not(self):
        hook = os.path.join(ROOT, ".claude", "hooks", "experiment_gate.py")
        env = dict(os.environ, CLAUDE_PROJECT_DIR=ROOT)
        def invoke(command):
            payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
            return subprocess.run([sys.executable, hook], input=payload, text=True,
                                  capture_output=True, cwd=ROOT, env=env)
        self.assertEqual(invoke("bash <<EOF\n./run.sh train\nEOF").returncode, 2)
        self.assertEqual(invoke("cat <<EOF\n./run.sh train\nEOF").returncode, 0)

    def test_missing_handoff_is_optional_on_first_close(self):
        hook = os.path.join(ROOT, ".claude", "hooks", "session_close_gate.py")
        with tempfile.TemporaryDirectory() as root:
            state = os.path.join(root, "report")
            os.makedirs(state)
            for name in ("discussion.md", "issue.md", "result.md", "version.md"):
                with open(os.path.join(state, name), "w", encoding="utf-8") as handle:
                    handle.write("# template\n")
            payload = json.dumps({"stop_hook_active": False})
            proc = subprocess.run([sys.executable, hook], input=payload, text=True,
                                  capture_output=True, env=dict(os.environ, CLAUDE_PROJECT_DIR=root))
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout, "")

    def test_codex_discovers_project_guidance_and_skills(self):
        if not shutil_which("codex"):
            self.skipTest("codex unavailable")
        proc = subprocess.run(["codex", "debug", "prompt-input", "test"], cwd=ROOT,
                              capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Codex AI research conductor-orchestrator", proc.stdout)
        self.assertIn("root conductor-orchestrator", proc.stdout)
        self.assertIn("codex-specialist-core", proc.stdout)

    def test_codex_root_conductor_topology_is_single_hop_and_bounded(self):
        with open(os.path.join(ROOT, "AGENTS.md"), encoding="utf-8") as handle:
            agents = handle.read()
        with open(os.path.join(ROOT, ".codex", "ORCHESTRATION.md"), encoding="utf-8") as handle:
            codex = handle.read()
        with open(os.path.join(ROOT, ".codex", "config.toml"), encoding="utf-8") as handle:
            config = handle.read()
        agents_flat = " ".join(agents.split())
        codex_flat = " ".join(codex.split())
        self.assertIn("root Codex thread is both conductor and orchestrator", agents_flat)
        self.assertIn("Never spawn a coordinator, conductor, or orchestrator subagent", agents_flat)
        self.assertIn("Specialists never spawn agents", agents_flat)
        self.assertIn("register the exact BRIEF", agents_flat)
        self.assertIn("root Codex conductor-orchestrator", codex_flat)
        self.assertIn("Use two to four specialists concurrently only", codex_flat)
        self.assertIn("Checkpoint with the user before eight dispatches", codex_flat)
        self.assertRegex(config, r"(?m)^max_depth\s*=\s*1\s*$")
        self.assertRegex(config, r"(?m)^max_threads\s*=\s*4\s*$")
        self.assertRegex(config, r"(?m)^multi_agent_v2\s*=\s*false\s*$")
        self.assertNotIn("[agents.orchestrator]", config)
        direct_dispatch_edges = len(CODEX_ROLES)
        layered_dispatch_edges = direct_dispatch_edges + 1
        self.assertLess(direct_dispatch_edges, layered_dispatch_edges)

    def test_provider_control_planes_are_isolated(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, ".orchestration", "isolation.py")],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        for name in ("discussion.md", "result.md", "error.md", "issue.md", "version.md", "CODEX.md"):
            self.assertFalse(os.path.exists(os.path.join(ROOT, name)), name)

    def test_installed_codex_supports_quality_fleet(self):
        if not shutil_which("codex"):
            self.skipTest("codex unavailable")
        files = {role: launcher.agent_path("quality", role) for role in CODEX_ROLES}
        launcher.validate_codex(files, *launcher.PRESETS["quality"])
        catalog = launcher.codex_catalog()
        for root_model, _ in launcher.PRESETS.values():
            self.assertIn(catalog[root_model]["multi_agent_version"], (None, "v1"))
        launcher.validate_codex_mcp()


def shutil_which(name):
    from shutil import which
    return which(name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
