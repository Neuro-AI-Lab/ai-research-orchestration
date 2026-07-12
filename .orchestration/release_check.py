#!/usr/bin/env python3
"""Fail-closed distribution checks for the research orchestration template."""

import json
import os
import re
import subprocess
import sys
from urllib.parse import urlsplit


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DOCS = ("discussion.md", "result.md", "error.md", "version.md", "CODEX.md")
RESEARCH_DOCS = tuple(
    ".{}/templates/research/{}".format(backend, name)
    for backend in ("codex", "claude")
    for name in ("discussion.md", "result.md", "error.md", "version.md")
)
REQUIRED = (
    "README.md", "README.ko.md", "SETUP.md", "SETUP.ko.md", "AGENTS.md", "CLAUDE.md",
    "SECURITY.md", "SECURITY.ko.md", "CONTRIBUTING.md", "orchestrate", ".mcp.json",
    ".codex/README.md", ".codex/ORCHESTRATION.md", ".codex/config.toml",
    ".codex/hooks/audit_event.py", ".codex/scripts/orchestration_audit.py",
    ".claude/README.md", ".orchestration/launcher.py", ".orchestration/isolation.py",
    ".orchestration/validate_system.py",
)
PUBLIC_DOCS = (
    "README.md", "README.ko.md", "SETUP.md", "SETUP.ko.md", "SECURITY.md",
    "SECURITY.ko.md", "CONTRIBUTING.md", "docs/AI_RESEARCH_PROMPTS.md",
    "docs/AI_RESEARCH_PROMPTS.ko.md", "docs/COMPATIBILITY.md",
    "docs/COMPATIBILITY.ko.md", "docs/FEATURES.md", "docs/FEATURES.ko.md",
    "docs/RELEASING.md", "docs/RELEASING.ko.md",
)
INTERNAL_PREFIXES = (
    ".orchestration/evals/", ".orchestration/reports/", "evaluation/orchestration/",
    "tests/repro/", "docs/internal/", "docs/validation/",
)
INTERNAL_FILES = {
    ".claude/prompts/orchestration-evals.md", "docs/orchestration-benchmark.md",
    "examples/toy-sentiment/EXAMPLE_ENTRIES.md",
    "examples/toy-sentiment/sample_output.txt",
}
REAL_ENTRY = re.compile(
    r"(?m)^## \[(?:HYP|RES|DATASET|REV|QA|ADR|PLAN|STATE|REPORT|EXP|BUG|VAL|VER|CLEAN)-\d"
)
SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"olp_[A-Za-z0-9_-]{20,}"),
)


def run(*args):
    return subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=False)


def candidate_files():
    proc = run("git", "ls-files", "-co", "--exclude-standard")
    if proc.returncode:
        return []
    return [name for name in proc.stdout.splitlines()
            if os.path.isfile(os.path.join(ROOT, name))]


def main():
    failures = []
    warnings = []

    def fail(message):
        failures.append(message)
        print("FAIL " + message)

    def warn(message):
        warnings.append(message)
        print("WARN " + message)

    def passed(message):
        print("PASS " + message)

    for path in REQUIRED:
        if os.path.isfile(os.path.join(ROOT, path)):
            passed(path + " present")
        else:
            fail(path + " missing")

    for path in PUBLIC_DOCS:
        try:
            with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
                content = handle.read()
        except OSError as exc:
            fail("{} unreadable: {}".format(path, exc))
            continue
        if "## CODEX" not in content or "## CLAUDE" not in content:
            fail(path + " must keep separate CODEX and CLAUDE sections")
        elif any(token in content for token in (
                "evaluation/orchestration", ".orchestration/evals",
                "orchestration-benchmark")):
            fail(path + " contains maintainer-only validation history")
        else:
            passed(path + " separates CODEX and CLAUDE guidance")

    for path in ("orchestrate", "setup.sh", "run.sh", "evaluate.sh"):
        full = os.path.join(ROOT, path)
        if not os.path.isfile(full) or os.path.getsize(full) == 0:
            fail(path + " is missing or empty")
        elif not os.access(full, os.X_OK):
            fail(path + " is not executable")
        else:
            passed(path + " is non-empty and executable")

    runtime_programs = []
    for backend in ("codex", "claude"):
        for directory in ("hooks", "scripts"):
            base = os.path.join(ROOT, "." + backend, directory)
            try:
                names = os.listdir(base)
            except OSError:
                names = []
            runtime_programs.extend(
                os.path.join("." + backend, directory, name)
                for name in names if name.endswith((".py", ".sh"))
            )
    unusable = []
    for path in runtime_programs:
        full = os.path.join(ROOT, path)
        if not os.path.isfile(full) or os.path.getsize(full) == 0 or not os.access(full, os.X_OK):
            unusable.append(path)
    if unusable:
        fail("provider runtime programs are empty or non-executable: " + ", ".join(unusable))
    else:
        passed("provider hooks and scripts are non-empty and executable")

    for path in ROOT_DOCS:
        if os.path.exists(os.path.join(ROOT, path)):
            fail(path + " is a forbidden legacy shared control file")
        else:
            passed(path + " absent (provider state is isolated)")

    for path in RESEARCH_DOCS:
        try:
            with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
                content = handle.read()
        except OSError as exc:
            fail("{} unreadable: {}".format(path, exc))
            continue
        if REAL_ENTRY.search(content):
            fail(path + " contains real research/session entries; reset from its provider template")
        else:
            passed(path + " contains template content only")

    memory_specs = tuple(("codex", role) for role in ("conductor", "brainstorm", "critic"))
    memory_specs += tuple(("claude", role) for role in ("orchestrator", "brainstorm", "critic"))
    for backend, role in memory_specs:
        seed = os.path.join(ROOT, "." + backend, "templates", "memory", role, "MEMORY.md")
        try:
            with open(seed, encoding="utf-8") as handle:
                seed_content = handle.read()
        except OSError as exc:
            fail("{} memory template check failed for {}: {}".format(backend, role, exc))
            continue
        if REAL_ENTRY.search(seed_content):
            fail("{} {} memory template contains live research entries".format(backend, role))
        else:
            passed("{} {} memory template is clean".format(backend, role))

    tracked = set(run("git", "ls-files").stdout.splitlines())
    for private in (
        ".claude/settings.local.json", ".claude/state/handoff.json",
        ".codex/settings.local.json", ".codex/state/handoff.json",
        ".orchestration/config.local.json",
    ):
        if private in tracked:
            fail(private + " is tracked")
        else:
            passed(private + " is not tracked")

    ignore_probes = (
        ".orchestration/config.local.json", ".orchestration/runs/probe.json",
        ".orchestration/evals/probe.json", ".orchestration/reports/probe.json",
        ".codex/settings.local.json", ".codex/state/handoff.json",
        ".codex/research/probe.md", ".codex/memory/probe/MEMORY.md",
        ".codex/runs/probe.json", ".claude/settings.local.json",
        ".claude/state/handoff.json", ".claude/research/probe.md",
        ".claude/agent-memory/probe/MEMORY.md", ".claude/runs/probe.json",
        "data/probe.json", "experiments/codex/probe.json", "analysis/codex/probe.json",
        "papers/notes/codex/probe.md", "tests/repro/probe.py",
        "docs/validation/probe.md",
    )
    not_ignored = [
        path for path in ignore_probes if run("git", "check-ignore", "-q", path).returncode
    ]
    if not_ignored:
        fail("private/internal paths are not ignored: " + ", ".join(not_ignored))
    else:
        passed("private state, generated artifacts, and maintainer history are ignored")

    tracked_live = sorted(
        name for name in tracked
        if name.startswith((
            ".claude/research/", ".claude/agent-memory/",
            ".claude/runs/", ".codex/research/", ".codex/memory/", ".codex/runs/",
        ))
    )
    if tracked_live:
        fail("live provider state/memory is tracked: " + ", ".join(tracked_live[:6]))
    else:
        passed("live provider state and memory are untracked")

    candidates = set(candidate_files())
    internal = sorted(
        name for name in candidates
        if name in INTERNAL_FILES or name.startswith(INTERNAL_PREFIXES)
    )
    if internal:
        fail("maintainer development/validation history is distribution-visible: "
             + ", ".join(internal[:6]))
    else:
        passed("maintainer development/validation history is excluded")

    tests = [name for name in candidate_files() if name.startswith("tests/")]
    if not tests:
        fail("no tracked/candidate tests found under tests/")
    else:
        ignored = [name for name in tests if run("git", "check-ignore", "-q", name).returncode == 0]
        if ignored:
            fail("research tests are ignored: " + ", ".join(ignored[:3]))
        else:
            passed("research tests are distribution-visible")

    remotes = run("git", "remote", "-v")
    if remotes.returncode == 0:
        unsafe = False
        for line in remotes.stdout.splitlines():
            fields = line.split()
            if len(fields) < 2:
                continue
            parsed = urlsplit(fields[1])
            if parsed.scheme in {"http", "https"} and (parsed.username or parsed.password):
                unsafe = True
        if unsafe:
            fail("a Git remote URL embeds credentials")
        else:
            passed("Git remote URLs contain no embedded credentials")

    secret_hits = []
    for path in candidate_files():
        full = os.path.join(ROOT, path)
        try:
            if os.path.getsize(full) > 2_000_000:
                continue
            with open(full, encoding="utf-8", errors="ignore") as handle:
                content = handle.read()
        except OSError:
            continue
        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            secret_hits.append(path)
    if secret_hits:
        fail("credential-like values found in: " + ", ".join(secret_hits))
    else:
        passed("no common credential patterns in distribution candidates")

    for path in (".mcp.json", ".claude/settings.json",
                 ".claude/settings.local.json.example", ".claude/state/handoff.json.example",
                 ".codex/settings.local.json.example", ".codex/state/handoff.json.example"):
        try:
            with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
                json.load(handle)
            passed(path + " valid JSON")
        except (OSError, ValueError) as exc:
            fail("{} invalid JSON: {}".format(path, exc))

    diff = run("git", "diff", "--check")
    if diff.returncode:
        fail("git diff --check failed")
    else:
        passed("git diff --check")
    staged_diff = run("git", "diff", "--cached", "--check")
    if staged_diff.returncode:
        fail("git diff --cached --check failed")
    else:
        passed("git diff --cached --check")

    isolation = run(sys.executable, ".orchestration/isolation.py")
    if isolation.returncode:
        fail("provider isolation failed:\n" + isolation.stdout.strip())
    else:
        passed("provider control planes and research state are isolated")

    live_memory = [name for name in candidate_files()
                   if name.startswith((".claude/agent-memory/", ".codex/memory/"))]
    if live_memory:
        fail("live provider memory is distribution-visible: " + ", ".join(live_memory))

    print("\nRelease check: {} failure(s), {} warning(s)".format(len(failures), len(warnings)))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
