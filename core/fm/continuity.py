"""Deterministic continuity checks (`fm check continuity`).

Checks only what can be checked mechanically; judgement calls (screen
direction, eyelines, emotional continuity) belong to the qa-supervisor's
review. Findings: FAIL = contradicts canon or references something that does
not exist; WARN = likely problem worth a look.
"""
from __future__ import annotations

from dataclasses import dataclass

from .project import Loaded

DURATION_TOLERANCE = 0.15  # shot total may differ from the brief's duration by ±15%

# continuity canon value key -> shot.environment field
_ENV_KEYS = {"weather": "weather", "time": "time_of_day", "time_of_day": "time_of_day",
             "location": "location"}


@dataclass
class ContinuityFinding:
    level: str  # FAIL | WARN
    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.level:4} {self.where}: {self.message}"


def _norm(v) -> str:
    return str(v).strip().lower()


def check_continuity(loaded: Loaded) -> list[ContinuityFinding]:
    out: list[ContinuityFinding] = []
    chars = {cid.split(".")[1] for cid in loaded.canon if cid.startswith("characters.")}
    scenes = loaded.scene_index.scenes if loaded.scene_index else []
    scene_ids = {s.scene_id for s in scenes}

    # canon continuity entries by the scope they apply to
    by_target: dict[str, list] = {}
    for cid, item in loaded.canon.items():
        if item.entry.domain != "continuity" or not isinstance(item.entry.value, dict):
            continue
        for t in item.entry.applies_to:
            by_target.setdefault(t, []).append(item.entry)

    for sid, it in sorted(loaded.shots.items()):
        s = it.spec
        where = f"shot:{sid}"
        for ch in s.characters:
            if ch.id not in chars:
                out.append(ContinuityFinding("FAIL", where, f"character '{ch.id}' has no canon entries"))
        if scene_ids and s.scene_id not in scene_ids:
            out.append(ContinuityFinding("WARN", where, f"scene {s.scene_id} is not in SCENES.yaml"))
        env = s.environment
        for target in (s.shot_id, s.scene_id, s.sequence_id):
            for entry in by_target.get(target or "", []):
                for key, field in _ENV_KEYS.items():
                    if key not in entry.value:
                        continue
                    expected = _norm(entry.value[key])
                    actual = getattr(env, field, None) if env else None
                    if actual is None:
                        out.append(ContinuityFinding(
                            "WARN", where, f"{entry.id} sets {key}='{entry.value[key]}' but the shot has no "
                                           f"environment.{field}"))
                    elif expected not in _norm(actual):
                        out.append(ContinuityFinding(
                            "FAIL", where, f"environment.{field}='{actual}' contradicts {entry.id} "
                                           f"({key}='{entry.value[key]}')"))

    # scene index vs shots
    for sc in scenes:
        shots_in = [it for it in loaded.shots.values() if it.spec.scene_id == sc.scene_id]
        if loaded.shots and not shots_in:
            out.append(ContinuityFinding("WARN", f"scene:{sc.scene_id}", "scene has no shots"))
        for it in shots_in:
            env = it.spec.environment
            for field in ("time_of_day", "weather"):
                want = getattr(sc, field)
                have = getattr(env, field, None) if env else None
                if want and have and _norm(want) not in _norm(have):
                    out.append(ContinuityFinding(
                        "WARN", f"shot:{it.spec.shot_id}",
                        f"environment.{field}='{have}' differs from SCENES.yaml {sc.scene_id} ({want})"))

    # running time vs brief
    if loaded.shots and loaded.brief is not None:
        f = loaded.brief.fields.get("duration_s")
        if f is not None and f.status != "unknown" and isinstance(f.value, (int, float)) and f.value > 0:
            total = sum(it.spec.duration_s for it in loaded.shots.values())
            lo, hi = f.value * (1 - DURATION_TOLERANCE), f.value * (1 + DURATION_TOLERANCE)
            if not lo <= total <= hi:
                out.append(ContinuityFinding(
                    "WARN", "film", f"shots total {total:g}s vs brief duration {f.value:g}s "
                                    f"(tolerance ±{DURATION_TOLERANCE:.0%})"))
    return out
