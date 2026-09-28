import os
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """An isolated copy of the repository skeleton (config + templates)."""
    root = tmp_path / "film_maker"
    shutil.copytree(REPO / "config", root / "config")
    shutil.copytree(REPO / "templates", root / "templates")
    (root / "projects").mkdir()
    monkeypatch.setenv("FM_ROOT", str(root))
    monkeypatch.setenv("FM_ACTOR", "agent:test")
    monkeypatch.setenv("FM_FIXED_TIME", "2026-01-01T00:00:00Z")
    monkeypatch.delenv("FM_PROJECT", raising=False)
    monkeypatch.chdir(root)
    return root


@pytest.fixture
def sandbox(repo):
    from fm.ops import init_project
    return init_project(repo, "last_signal", "Last Signal", sandbox=True)


@pytest.fixture
def production(repo):
    from fm.ops import init_project
    return init_project(repo, "real_film", "Real Film", sandbox=False)


def set_actor(monkeypatch, actor):
    monkeypatch.setenv("FM_ACTOR", actor)
