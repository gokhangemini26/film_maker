"""Who is acting, and what they are allowed to do.

Agents may propose, analyse, generate, revise and record builds. Only a
human may approve, lock, decide change requests, or authorize expensive
renders. Human-only actions require an interactive terminal and a typed
confirmation token, so a non-interactive tool call (how agents run
commands) cannot perform them. Sandbox projects (demos/tests, flagged at
creation and never convertible) may simulate the confirmation; the ledger
marks such records `simulated`.
"""
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable

from .errors import AuthorityError

ACTOR_KINDS = ("human", "agent", "system")


@dataclass(frozen=True)
class Actor:
    kind: str
    name: str

    def __str__(self) -> str:
        return f"{self.kind}:{self.name}"

    @property
    def is_human(self) -> bool:
        return self.kind == "human"


def _git_user() -> str:
    try:
        out = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True,
                             timeout=5)
        name = out.stdout.strip()
        return name.lower().replace(" ", "_") if name else "user"
    except (OSError, subprocess.SubprocessError):
        return "user"


def _interactive() -> bool:
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except (AttributeError, ValueError):
        return False


def current_actor() -> Actor:
    """FM_ACTOR=<kind>:<name> wins. Otherwise: an interactive terminal is a
    human; anything non-interactive is treated as an unattended agent."""
    raw = os.environ.get("FM_ACTOR", "").strip()
    if raw:
        kind, _, name = raw.partition(":")
        if kind not in ACTOR_KINDS or not name:
            raise AuthorityError(f"FM_ACTOR must be kind:name with kind in {ACTOR_KINDS}, got '{raw}'")
        return Actor(kind, name)
    if _interactive():
        return Actor("human", _git_user())
    return Actor("agent", "unattended")


# Tests replace this to simulate a person typing at a terminal.
_prompt: Callable[[str], str] = input


def assert_human(action: str) -> Actor:
    """Fail fast, before any state checks, when a non-human requests a human-only action."""
    actor = current_actor()
    if not actor.is_human:
        raise AuthorityError(
            f"'{action}' is a human-only action; actor is {actor}. "
            "Agents may propose and prepare, but a person must run this in a terminal."
        )
    return actor


def require_human(action: str, token: str, *, sandbox: bool, sandbox_confirm: bool) -> dict:
    """Return ledger payload fields describing how the human confirmed.

    Raises AuthorityError unless a human confirms interactively (or, only in a
    sandbox project, explicitly passes --sandbox-confirm).
    """
    assert_human(action)
    if sandbox_confirm:
        if not sandbox:
            raise AuthorityError("--sandbox-confirm is only valid in sandbox projects")
        return {"confirmation": "sandbox-simulated", "simulated": True}
    if not _interactive() and _prompt is input:
        raise AuthorityError(
            f"'{action}' needs an interactive terminal for confirmation "
            "(non-interactive calls are how agents run commands)."
        )
    typed = _prompt(f"{action}\nType '{token}' to confirm: ").strip()
    if typed != token:
        raise AuthorityError(f"confirmation did not match '{token}'; nothing was changed")
    return {"confirmation": "typed", "simulated": False}
