"""Current experiment-gate behavior, without release-history fixtures."""

import pytest

from tests.orchestration.gate_test_utils import run_hook


MENTION_ONLY = (
    "cat run.sh",
    "bash -n evaluate.sh",
    "grep -E 'run.sh|evaluate.sh' README.md",
    "echo 'use (run.sh) later'",
    "grep -rn 'python models/train.py' README.md",
    "wc -l setup.sh run.sh evaluate.sh",
    "cat <<EOF\n./run.sh train\nEOF",
)

REAL_LAUNCHES = (
    "./run.sh train",
    "CUDA_VISIBLE_DEVICES=0 ./run.sh train",
    "bash run.sh train",
    "true && ./evaluate.sh test",
    "python3 models/train.py",
    "x=$(./run.sh train)",
    "bash <<EOF\n./run.sh train\nEOF",
)


@pytest.mark.parametrize("backend", ("codex", "claude"))
@pytest.mark.parametrize("command", MENTION_ONLY)
def test_read_only_mentions_are_allowed(backend, command):
    proc = run_hook(command, backend=backend)
    assert proc.returncode == 0, (backend, command, proc.stderr)


@pytest.mark.parametrize("backend", ("codex", "claude"))
@pytest.mark.parametrize("command", REAL_LAUNCHES)
def test_real_launches_require_research_attestations(backend, command):
    proc = run_hook(command, backend=backend)
    assert proc.returncode == 2, (backend, command, proc.stderr)
    assert "GATE" in proc.stderr


@pytest.mark.parametrize("backend", ("codex", "claude"))
def test_override_must_cite_an_existing_adr_on_every_launch_segment(backend):
    missing = run_hook("GATE_OVERRIDE=ADR-999 ./run.sh test", backend=backend)
    assert missing.returncode == 2
    assert "ADR-999" in missing.stderr

    valid = run_hook("GATE_OVERRIDE=ADR-001 ./run.sh test", backend=backend)
    assert valid.returncode == 0, valid.stderr

    mixed = run_hook(
        "./run.sh train; GATE_OVERRIDE=ADR-001 ./run.sh test", backend=backend
    )
    assert mixed.returncode == 2, mixed.stderr

    complete = run_hook(
        "GATE_OVERRIDE=ADR-001 ./run.sh train; "
        "GATE_OVERRIDE=ADR-001 ./run.sh test",
        backend=backend,
    )
    assert complete.returncode == 0, complete.stderr
