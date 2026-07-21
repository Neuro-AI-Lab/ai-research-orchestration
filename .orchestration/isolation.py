#!/usr/bin/env python3
"""Static provider-isolation checks for the dual distribution."""

import os
import re


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT_SUFFIXES = {".md", ".toml", ".json", ".py", ".sh", ".yaml", ".yml"}
ROOT_STATE = ("discussion.md", "result.md", "error.md", "issue.md", "version.md", "CODEX.md")

SURFACES = {
    "codex": (
        "AGENTS.md",
        "docs/orchestration/CODEX.md",
        "docs/orchestration/CODEX.ko.md",
        ".codex/ORCHESTRATION.md",
        ".codex/config.toml",
        ".codex/contracts",
        ".codex/fleets",
        ".codex/hooks",
        ".codex/prompts",
        ".codex/scripts",
        ".agents/skills",
    ),
    "claude": (
        "CLAUDE.md",
        ".mcp.json",
        "docs/orchestration/CLAUDE.md",
        "docs/orchestration/CLAUDE.ko.md",
        ".claude/settings.json",
        ".claude/agents",
        ".claude/fleets",
        ".claude/hooks",
        ".claude/prompts",
        ".claude/scripts",
        ".claude/skills",
    ),
}

FORBIDDEN = {
    "codex": re.compile(
        r"\.claude/|\.mcp\.json|\bCLAUDE\.md\b|"
        r"\b(?:Claude|Anthropic|Sonnet|Opus|Fable|Haiku)\b|"
        r"\borchestrator-opus\b",
        re.IGNORECASE,
    ),
    "claude": re.compile(
        r"\.codex/|\.agents/|\bAGENTS\.md\b|\bCodex\b|\bOpenAI\b|\bgpt-[\w.-]+",
        re.IGNORECASE,
    ),
}

UNSCOPED_STATE = re.compile(
    r"(?<![A-Za-z0-9_./])(?:discussion|result|error|issue|version)\.md\b"
)
VAGUE_STATE = re.compile(r"\broot (?:doc|document)s?\b", re.IGNORECASE)
LEGACY_CODEX_PATH = re.compile(
    r"\.codex/research/|experiments/codex/|analysis/codex/|papers/notes/codex/|"
    r"(?<![A-Za-z0-9_.-])models/|(?<![A-Za-z0-9_.-])evaluation/"
)
CODEX_SPECIALISTS = {
    "brainstorm", "data", "critic", "developer", "qa", "experiment-tracker",
    "filemanager", "writer",
}


def iter_files(surface):
    for relative in SURFACES[surface]:
        path = os.path.join(ROOT, relative)
        if os.path.isfile(path):
            yield relative, path
            continue
        if not os.path.isdir(path):
            continue
        for base, dirs, files in os.walk(path):
            dirs[:] = [name for name in dirs if name != "__pycache__"]
            for name in files:
                if os.path.splitext(name)[1].lower() not in TEXT_SUFFIXES:
                    continue
                full = os.path.join(base, name)
                yield os.path.relpath(full, ROOT), full


def provider_isolation_errors(active_backend=None):
    if active_backend not in (None, "codex", "claude"):
        return ["unknown active provider: {}".format(active_backend)]
    errors = []
    for name in ROOT_STATE:
        if os.path.exists(os.path.join(ROOT, name)):
            errors.append("legacy shared control file exists at repository root: " + name)

    surfaces = (active_backend,) if active_backend else ("codex", "claude")
    for surface in surfaces:
        expected_prefix = "report/"
        for relative, path in iter_files(surface):
            try:
                with open(path, encoding="utf-8") as handle:
                    text = handle.read()
            except (OSError, UnicodeError) as exc:
                errors.append("{}: unreadable control file: {}".format(relative, exc))
                continue
            for line_number, line in enumerate(text.splitlines(), 1):
                forbidden = FORBIDDEN[surface].search(line)
                if forbidden:
                    errors.append(
                        "{}:{}: {} control plane contains forbidden provider token {!r}".format(
                            relative, line_number, surface, forbidden.group(0)
                        )
                    )
                unscoped = UNSCOPED_STATE.search(line)
                if unscoped and expected_prefix not in line:
                    errors.append(
                        "{}:{}: unscoped research-state reference {!r}".format(
                            relative, line_number, unscoped.group(0)
                        )
                    )
                vague = VAGUE_STATE.search(line)
                if vague:
                    errors.append(
                        "{}:{}: ambiguous research-state label {!r}; name the provider path".format(
                            relative, line_number, vague.group(0)
                        )
                    )
                if surface == "codex" and LEGACY_CODEX_PATH.search(line):
                    errors.append(
                        "{}:{}: Codex control plane contains a legacy workspace path".format(
                            relative, line_number
                        )
                    )
    if active_backend in (None, "codex"):
        config_path = os.path.join(ROOT, ".codex", "config.toml")
        try:
            with open(config_path, encoding="utf-8") as handle:
                config = handle.read()
        except OSError as exc:
            errors.append(".codex/config.toml: cannot verify Codex topology: {}".format(exc))
            config = ""
        if config and not re.search(r"(?m)^max_depth\s*=\s*1\s*$", config):
            errors.append(".codex/config.toml: Codex max_depth must be 1")
        if config and not re.search(r"(?m)^max_threads\s*=\s*4\s*$", config):
            errors.append(".codex/config.toml: Codex max_threads must be 4")
        if config and not re.search(r"(?m)^multi_agent_v2\s*=\s*false\s*$", config):
            errors.append(".codex/config.toml: Codex multi_agent_v2 must be disabled")
        if "[agents.orchestrator]" in config:
            errors.append(".codex/config.toml: root Codex must not configure an orchestrator subagent")

        legacy_templates = os.path.join(ROOT, ".codex", "templates", "research")
        if os.path.exists(legacy_templates):
            errors.append(".codex/templates/research: legacy Codex templates must not ship")

        for preset in ("quality", "balanced", "fast"):
            directory = os.path.join(ROOT, ".codex", "fleets", preset)
            try:
                actual = {
                    os.path.splitext(name)[0] for name in os.listdir(directory)
                    if name.endswith(".toml")
                }
            except OSError:
                actual = set()
            if actual != CODEX_SPECIALISTS:
                errors.append(
                    ".codex/fleets/{}: expected only eight Codex specialists; found {}".format(
                        preset, ", ".join(sorted(actual)) or "none"
                    )
                )
        prompts = os.path.join(ROOT, ".codex", "prompts", "roles")
        try:
            prompt_roles = {
                os.path.splitext(name)[0] for name in os.listdir(prompts) if name.endswith(".md")
            }
        except OSError:
            prompt_roles = set()
        if prompt_roles != CODEX_SPECIALISTS:
            errors.append(
                ".codex/prompts/roles: expected only eight Codex specialist specs; found {}".format(
                    ", ".join(sorted(prompt_roles)) or "none"
                )
            )
        conductor_seed = os.path.join(
            ROOT, ".codex", "templates", "memory", "conductor", "MEMORY.md"
        )
        if not os.path.isfile(conductor_seed):
            errors.append(".codex/templates/memory/conductor/MEMORY.md: missing conductor seed")
    return errors


def main():
    errors = provider_isolation_errors(os.environ.get("ORCHESTRATION_BACKEND"))
    for error in errors:
        print("FAIL " + error)
    if errors:
        print("Provider isolation: {} failure(s)".format(len(errors)))
        return 1
    print("Provider isolation: 0 failure(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
