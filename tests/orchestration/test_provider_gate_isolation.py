"""Each experiment gate must consume only its provider-owned research state."""

import json
import os
import subprocess
import sys
import tempfile

import pytest

from tests.orchestration.gate_test_utils import REPO_ROOT, run_hook


PASSED = """# discussion
## [DATASET-001] synthetic fixture | data
**Leakage audit:** passed
## [REV-001] synthetic plan | critic
**Severity:** major
**Gate:** passed
**Status:** resolved
## [QA-001] synthetic code check | qa
**Gate:** passed
**Status:** complete
"""


@pytest.mark.parametrize("backend", ("codex", "claude"))
def test_provider_accepts_its_own_positive_attestations(backend):
    proc = run_hook("./run.sh train", backend=backend, discussion=PASSED)
    assert proc.returncode == 0, (backend, proc.stderr)


@pytest.mark.parametrize("active", ("codex", "claude"))
def test_provider_ignores_legacy_provider_private_research_state(active):
    with tempfile.TemporaryDirectory() as root:
        active_dir = os.path.join(root, "report")
        legacy_dir = os.path.join(root, "." + active, "research")
        os.makedirs(active_dir)
        os.makedirs(legacy_dir)
        for base, discussion in ((active_dir, "# empty\n"), (legacy_dir, PASSED)):
            with open(os.path.join(base, "discussion.md"), "w", encoding="utf-8") as handle:
                handle.write(discussion)
            with open(os.path.join(base, "issue.md"), "w", encoding="utf-8") as handle:
                handle.write("# empty\n")
        payload = json.dumps({
            "tool_name": "Bash", "tool_input": {"command": "./run.sh train"}
        })
        variable = "CODEX_PROJECT_DIR" if active == "codex" else "CLAUDE_PROJECT_DIR"
        hook = os.path.join(REPO_ROOT, "." + active, "hooks", "experiment_gate.py")
        proc = subprocess.run(
            [sys.executable, hook], input=payload, text=True, capture_output=True,
            cwd=REPO_ROOT,
            env=dict(os.environ, ORCHESTRATION_BACKEND=active, **{variable: root}),
            check=False,
        )
        assert proc.returncode == 2, (active, proc.stderr)
        assert "no DATASET" in proc.stderr
