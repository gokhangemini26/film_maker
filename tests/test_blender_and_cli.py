"""Blender version gate and CLI behaviour (exit codes, refusals)."""
import pytest
from click.testing import CliRunner

from fm.blender import parse_version, require_blender
from fm.cli import cli
from fm.errors import BlenderVersionError


@pytest.mark.parametrize("out,version,series,lts", [
    ("Blender 5.2.1 LTS\n\tbuild date: ...", "5.2.1", "5.2", True),
    ("Blender 4.2.0\n", "4.2.0", "4.2", False),
    ("Blender 5.2\n", "5.2.0", "5.2", False),
])
def test_parse_version(out, version, series, lts):
    assert parse_version(out) == (version, series, lts)


def test_parse_version_garbage():
    with pytest.raises(BlenderVersionError):
        parse_version("command not found")


def test_require_blender_accepts_pinned_series(repo):
    info = require_blender(repo, _probe=lambda exe, t: "Blender 5.2.3 LTS")
    assert info.version == "5.2.3" and info.series == "5.2"


@pytest.mark.parametrize("other", ["Blender 5.1.0", "Blender 4.2.9 LTS", "Blender 5.3.0"])
def test_require_blender_refuses_other_series(repo, other):
    with pytest.raises(BlenderVersionError, match="Refusing"):
        require_blender(repo, _probe=lambda exe, t: other)


def test_require_blender_missing_executable(repo, monkeypatch):
    monkeypatch.setenv("FM_BLENDER", str(repo / "no_such_blender"))
    with pytest.raises(BlenderVersionError, match="not found"):
        require_blender(repo)


# ------------------------------------------------------------------ CLI
def run(*args):
    return CliRunner().invoke(cli, list(args), standalone_mode=False, catch_exceptions=True)


def test_cli_init_status_validate(repo):
    from fm.cli import main  # noqa: F401 - import check
    r = run("init", "demo_film", "--title", "Demo", "--sandbox")
    assert r.exception is None, r.output
    assert "SANDBOX" in r.output
    r = run("-p", "demo_film", "status")
    assert "current_phase: IDEA" in r.output
    r = run("-p", "demo_film", "validate")
    assert "0 error(s)" in r.output


def test_cli_agent_approval_is_refused_with_exit_3(repo, sandbox):
    import os
    import subprocess
    import sys
    env = {**os.environ, **{"FM_ROOT": str(repo), "FM_ACTOR": "agent:claude-code"}}
    p = subprocess.run([sys.executable, "-m", "fm.cli", "-p", "last_signal", "approve", "G1",
                        "--sandbox-confirm"], capture_output=True, text=True, env=env)
    assert p.returncode == 3, p.stderr
    assert "human-only" in p.stderr


def test_cli_validate_exit_code_on_error(repo, sandbox):
    import os
    import subprocess
    import sys
    (sandbox.canon_dir / "look.yaml").write_text("domain: look\nentries:\n  - id: BAD\n    statement: x\n")
    env = {**os.environ, "FM_ROOT": str(repo)}
    p = subprocess.run([sys.executable, "-m", "fm.cli", "-p", "last_signal", "validate", "-q"],
                       capture_output=True, text=True, env=env)
    assert p.returncode == 1
    assert "SCHEMA" in p.stdout
