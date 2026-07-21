"""Fail-closed provider-boundary and Codex-topology checks."""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "provider_isolation", ROOT / ".orchestration" / "isolation.py"
)
ISOLATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ISOLATION)


def configure_fixture(monkeypatch, tmp_path, codex_text, claude_text="provider control\n"):
    (tmp_path / "AGENTS.md").write_text(codex_text, encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text(claude_text, encoding="utf-8")
    config = tmp_path / ".codex" / "config.toml"
    config.parent.mkdir(parents=True)
    config.write_text("[agents]\nmax_threads = 4\nmax_depth = 1\n", encoding="utf-8")
    for preset in ("quality", "balanced", "fast"):
        fleet = tmp_path / ".codex" / "fleets" / preset
        fleet.mkdir(parents=True)
        for role in ISOLATION.CODEX_SPECIALISTS:
            (fleet / (role + ".toml")).write_text("# synthetic\n", encoding="utf-8")
    prompts = tmp_path / ".codex" / "prompts" / "roles"
    prompts.mkdir(parents=True)
    for role in ISOLATION.CODEX_SPECIALISTS:
        (prompts / (role + ".md")).write_text("# synthetic\n", encoding="utf-8")
    conductor = tmp_path / ".codex" / "templates" / "memory" / "conductor"
    conductor.mkdir(parents=True)
    (conductor / "MEMORY.md").write_text("# clean seed\n", encoding="utf-8")
    monkeypatch.setattr(ISOLATION, "ROOT", str(tmp_path))
    monkeypatch.setattr(
        ISOLATION, "SURFACES", {"codex": ("AGENTS.md",), "claude": ("CLAUDE.md",)}
    )


def test_distribution_control_planes_are_isolated():
    assert ISOLATION.provider_isolation_errors() == []


def test_codex_canonical_report_reference_is_allowed(monkeypatch, tmp_path):
    configure_fixture(monkeypatch, tmp_path, "Read report/result.md.\n")
    assert ISOLATION.provider_isolation_errors() == []


def test_cross_provider_reference_fails(monkeypatch, tmp_path):
    configure_fixture(monkeypatch, tmp_path, "Read .claude/agents/critic.md.\n")
    assert any(
        "forbidden provider token" in error
        for error in ISOLATION.provider_isolation_errors()
    )


def test_codex_canonical_plan_reference_is_allowed(monkeypatch, tmp_path):
    configure_fixture(monkeypatch, tmp_path, "Read plan/PRD.md.\n")
    assert ISOLATION.provider_isolation_errors() == []


def test_codex_reference_to_claude_owned_root_mcp_file_fails(monkeypatch, tmp_path):
    configure_fixture(monkeypatch, tmp_path, "Read .mcp.json for tools.\n")
    assert any(
        "forbidden provider token" in error
        for error in ISOLATION.provider_isolation_errors()
    )


def test_unscoped_state_and_artifact_paths_fail(monkeypatch, tmp_path):
    configure_fixture(
        monkeypatch, tmp_path,
        "Read result.md and inspect experiments/codex/EXP-NNN/, then update the root docs.\n",
    )
    errors = ISOLATION.provider_isolation_errors()
    assert any("unscoped research-state" in error for error in errors)
    assert any("legacy workspace path" in error for error in errors)
    assert any("ambiguous research-state label" in error for error in errors)


def test_codex_orchestrator_subagent_and_extra_depth_fail(monkeypatch, tmp_path):
    configure_fixture(monkeypatch, tmp_path, "provider control\n")
    config = tmp_path / ".codex" / "config.toml"
    config.write_text(
        "[agents]\nmax_threads = 4\nmax_depth = 2\n"
        "[agents.orchestrator]\nconfig_file = 'x'\n",
        encoding="utf-8",
    )
    errors = ISOLATION.provider_isolation_errors()
    assert any("max_depth must be 1" in error for error in errors)
    assert any("must not configure an orchestrator subagent" in error for error in errors)
