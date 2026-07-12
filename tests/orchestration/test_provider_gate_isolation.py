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


@pytest.mark.parametrize("active,other", (("codex", "claude"), ("claude", "codex")))
def test_provider_ignores_the_other_provider_state(active, other):
    with tempfile.TemporaryDirectory() as root:
        active_dir = os.path.join(root, "." + active, "research")
        other_dir = os.path.join(root, "." + other, "research")
        os.makedirs(active_dir)
        os.makedirs(other_dir)
        for base, discussion in ((active_dir, "# empty\n"), (other_dir, PASSED)):
            with open(os.path.join(base, "discussion.md"), "w", encoding="utf-8") as handle:
                handle.write(discussion)
            with open(os.path.join(base, "error.md"), "w", encoding="utf-8") as handle:
                handle.write("# empty\n")
        payload = json.dumps({
            "tool_name": "Bash", "tool_input": {"command": "./run.sh train"}
        })
        variable = "CODEX_PROJECT_DIR" if active == "codex" else "CLAUDE_PROJECT_DIR"
        hook = os.path.join(REPO_ROOT, "." + active, "hooks", "experiment_gate.py")
        proc = subprocess.run(
            [sys.executable, hook], input=payload, text=True, capture_output=True,
            cwd=REPO_ROOT, env=dict(os.environ, **{variable: root}), check=False,
        )
        assert proc.returncode == 2, (active, proc.stderr)
        assert "no DATASET" in proc.stderr
