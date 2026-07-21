"""Run one provider's experiment gate against isolated synthetic state."""

import json
import os
import subprocess
import sys
import tempfile


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DISCUSSION = """# discussion
## [ADR-001] synthetic override fixture | test
**Context:** exercise the documented override path
**Decision:** permit only the launch segment carrying this ADR
**Consequences:** synthetic fixture only
**Rollback:** remove the temporary fixture
**Linked:** tests/orchestration
---
"""


def run_hook(command, backend="codex", discussion=DISCUSSION, issue="# issue\n"):
    if backend not in {"codex", "claude"}:
        raise ValueError("unknown backend: " + backend)
    hook = os.path.join(REPO_ROOT, "." + backend, "hooks", "experiment_gate.py")
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    with tempfile.TemporaryDirectory() as root:
        state = os.path.join(root, "report")
        os.makedirs(state)
        with open(os.path.join(state, "discussion.md"), "w", encoding="utf-8") as handle:
            handle.write(discussion)
        with open(os.path.join(state, "issue.md"), "w", encoding="utf-8") as handle:
            handle.write(issue)
        variable = "CODEX_PROJECT_DIR" if backend == "codex" else "CLAUDE_PROJECT_DIR"
        return subprocess.run(
            [sys.executable, hook], input=payload, text=True, capture_output=True,
            env=dict(os.environ, ORCHESTRATION_BACKEND=backend, **{variable: root}),
            cwd=REPO_ROOT, check=False,
        )
