#!/usr/bin/env python3
"""Fail-closed distribution checks for the research orchestration template."""

import json
import os
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DOCS = ("discussion.md", "result.md", "error.md", "issue.md", "version.md", "CODEX.md")
RESEARCH_DOCS = tuple(
    ".{}/templates/report/{}".format(backend, name)
    for backend in ("codex", "claude")
    for name in ("discussion.md", "result.md", "issue.md", "version.md")
)
PLAN_TEMPLATES = (
    ".codex/templates/plan/PRD.md", ".codex/templates/plan/CHECKLIST.md",
    ".claude/templates/plan/PRD.md", ".claude/templates/plan/CHECKLIST.md",
)
WORKSPACE_FILES = (
    "plan/PRD.md", "plan/CHECKLIST.md", "report/discussion.md", "report/issue.md",
    "report/result.md", "report/version.md",
)
WORKSPACE_DIRS = (
    "plan", "report", "data", "model", "experiments", "analysis", "functionals", "utils",
)
PUBLIC_DOCS = (
    "README.md", "README.ko.md",
    "docs/orchestration/CODEX.md", "docs/orchestration/CODEX.ko.md",
    "docs/orchestration/CLAUDE.md", "docs/orchestration/CLAUDE.ko.md",
    "docs/orchestration/MAINTAINERS.md", "docs/orchestration/MAINTAINERS.ko.md",
)
PROVIDER_DOCS = {
    "codex": ("docs/orchestration/CODEX.md", "docs/orchestration/CODEX.ko.md"),
    "claude": ("docs/orchestration/CLAUDE.md", "docs/orchestration/CLAUDE.ko.md"),
}
DOC_PAIRS = (
    ("README.md", "README.ko.md"),
    ("docs/orchestration/CODEX.md", "docs/orchestration/CODEX.ko.md"),
    ("docs/orchestration/CLAUDE.md", "docs/orchestration/CLAUDE.ko.md"),
    ("docs/orchestration/MAINTAINERS.md", "docs/orchestration/MAINTAINERS.ko.md"),
)
LEGACY_PUBLIC_DOCS = (
    "SETUP.md", "SETUP.ko.md", "SECURITY.md", "SECURITY.ko.md", "CONTRIBUTING.md",
    "PROJECT_MAP.md",
    "docs/AI_RESEARCH_PROMPTS.md", "docs/AI_RESEARCH_PROMPTS.ko.md",
    "docs/COMPATIBILITY.md", "docs/COMPATIBILITY.ko.md",
    "docs/FEATURES.md", "docs/FEATURES.ko.md",
    "docs/RELEASING.md", "docs/RELEASING.ko.md",
    ".codex/README.md", ".codex/docs/integrations/ZOTERO.md",
    ".codex/docs/integrations/OVERLEAF.md", ".claude/README.md",
    ".claude/ZOTERO.md", ".claude/OVERLEAF.md",
)
REQUIRED = PUBLIC_DOCS + (
    "AGENTS.md", "CLAUDE.md", "LICENSE", "requirements.txt",
    "orchestrate", "setup.sh", "run.sh", "evaluate.sh", ".mcp.json",
    ".codex/ORCHESTRATION.md", ".codex/config.toml",
    ".codex/hooks/audit_event.py", ".codex/scripts/orchestration_audit.py",
    ".claude/settings.json", *PLAN_TEMPLATES, *WORKSPACE_FILES,
    ".orchestration/launcher.py", ".orchestration/isolation.py",
    ".orchestration/project_map.json", ".orchestration/validate_system.py",
)
INTERNAL_PREFIXES = (
    ".orchestration/evals/", ".orchestration/reports/", "evaluation/orchestration/",
    "tests/repro/", "docs/internal/", "docs/validation/",
)
INTERNAL_FILES = {
    ".claude/prompts/orchestration-evals.md", "docs/orchestration-benchmark.md",
}
REAL_ENTRY = re.compile(
    r"(?m)^## \[(?:HYP|RES|DATASET|REV|QA|ADR|PLAN|STATE|REPORT|EXP|BUG|VAL|VER|CLEAN)-\d"
)
SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"olp_[A-Za-z0-9_-]{20,}"),
)
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


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

    for path in WORKSPACE_DIRS:
        if os.path.isdir(os.path.join(ROOT, path)):
            passed(path + "/ workspace directory present")
        else:
            fail(path + "/ workspace directory missing")

    public_content = {}
    for path in PUBLIC_DOCS:
        try:
            with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
                content = handle.read()
        except OSError as exc:
            fail("{} unreadable: {}".format(path, exc))
            continue
        public_content[path] = content
        if any(token in content for token in (
                "evaluation/orchestration", ".orchestration/evals",
                "orchestration-benchmark")):
            fail(path + " contains maintainer-only validation history")
        else:
            passed(path + " contains no maintainer-only validation history")

    for backend, paths in PROVIDER_DOCS.items():
        forbidden = re.compile(r"\bClaude\b", re.IGNORECASE) if backend == "codex" else re.compile(
            r"\bCodex\b", re.IGNORECASE
        )
        for path in paths:
            content = public_content.get(path, "")
            if forbidden.search(content):
                fail(path + " crosses the provider documentation boundary")
            elif content:
                passed(path + " is provider-isolated")

    for readme in ("README.md", "README.ko.md"):
        content = public_content.get(readme, "")
        missing = [path for paths in PROVIDER_DOCS.values() for path in paths
                   if (path.endswith(".ko.md") == readme.endswith(".ko.md")) and path not in content]
        if missing:
            fail(readme + " does not link every provider guide for its language")
        elif content:
            passed(readme + " routes users to both provider guides")

    for english, korean in DOC_PAIRS:
        english_sections = len(re.findall(r"(?m)^## ", public_content.get(english, "")))
        korean_sections = len(re.findall(r"(?m)^## ", public_content.get(korean, "")))
        if not english_sections or english_sections != korean_sections:
            fail("{} and {} have mismatched section structure".format(english, korean))
        else:
            passed("{} and {} have paired section structure".format(english, korean))

    broken_links = []
    for path, content in public_content.items():
        for match in MARKDOWN_LINK.finditer(content):
            target = match.group(1).strip()
            if not target or target.startswith("#"):
                continue
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc:
                continue
            local = unquote(parsed.path)
            if not local:
                continue
            base = ROOT if local.startswith("/") else os.path.join(ROOT, os.path.dirname(path))
            resolved = os.path.normpath(os.path.join(base, local.lstrip("/")))
            if not os.path.exists(resolved):
                broken_links.append("{} -> {}".format(path, target))
    if broken_links:
        fail("broken local documentation links: " + ", ".join(broken_links))
    else:
        passed("public documentation local links resolve")

    for path in LEGACY_PUBLIC_DOCS:
        if os.path.exists(os.path.join(ROOT, path)):
            fail(path + " is a redundant legacy distribution document")
        else:
            passed(path + " absent (guidance is consolidated)")

    allowed_root_markdown = {"README.md", "README.ko.md", "AGENTS.md", "CLAUDE.md"}
    extra_root_markdown = sorted(
        path for path in candidate_files()
        if "/" not in path and path.endswith(".md") and path not in allowed_root_markdown
    )
    if extra_root_markdown:
        fail("unexpected root Markdown documents: " + ", ".join(extra_root_markdown))
    else:
        passed("root Markdown footprint is limited to entry policy and overview files")

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

    for path in RESEARCH_DOCS + PLAN_TEMPLATES + WORKSPACE_FILES:
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
        ".claude/state/handoff.json",
        ".claude/agent-memory/probe/MEMORY.md", ".claude/runs/probe.json",
        "tests/repro/probe.py",
        "docs/validation/probe.md",
        "experiments/runs/EXP-999/status.json",
    )
    not_ignored = [
        path for path in ignore_probes if run("git", "check-ignore", "-q", path).returncode
    ]
    if not_ignored:
        fail("private/internal paths are not ignored: " + ", ".join(not_ignored))
    else:
        passed("private state, generated artifacts, and maintainer history are ignored")

    wrongly_ignored_workspace = [
        path for path in (
            "plan/PRD.md", "report/discussion.md", "data/example.csv", "model/model.py",
            "experiments/train.py", "analysis/analyze.py", "functionals/loss.py", "utils/io.py",
        )
        if run("git", "check-ignore", "-q", path).returncode == 0
    ]
    if wrongly_ignored_workspace:
        fail("canonical workspace paths are ignored: " + ", ".join(wrongly_ignored_workspace))
    else:
        passed("canonical workspace paths are distribution-visible")

    tracked_live = sorted(
        name for name in tracked
        if name.startswith((
            ".claude/agent-memory/",
            ".claude/runs/", ".codex/research/", ".codex/memory/", ".codex/runs/",
        ))
    )
    if tracked_live:
        fail("live provider state/memory is tracked: " + ", ".join(tracked_live[:6]))
    else:
        passed("live provider state and memory are untracked")

    # plan/ and report/ ship as clean workspace seeds; they must never carry real entries.
    dirty_workspace = []
    for name in sorted(candidate_files()):
        if not name.startswith(("plan/", "report/")) or not name.endswith(".md"):
            continue
        try:
            with open(os.path.join(ROOT, name), encoding="utf-8") as handle:
                if REAL_ENTRY.search(handle.read()):
                    dirty_workspace.append(name)
        except OSError:
            dirty_workspace.append(name)
    if dirty_workspace:
        fail("shipped workspace seeds contain real research entries: "
             + ", ".join(dirty_workspace[:6]))
    else:
        passed("plan/ and report/ ship as clean workspace seeds")

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
                 ".codex/settings.local.json.example", ".codex/state/handoff.json.example",
                 ".orchestration/project_map.json"):
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
