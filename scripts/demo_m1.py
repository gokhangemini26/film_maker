"""M1 demonstration: runs the real `fm` CLI against a sandbox project.

    python scripts/demo_m1.py            # creates projects/m1_demo (sandbox)
    python scripts/demo_m1.py --clean    # remove it first

Human decisions are simulated with --sandbox-confirm, which only sandbox
projects accept; the ledger marks them `simulated`. The last section shows
the same approval being refused in a production project.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from fm import ops, testing  # noqa: E402
from fm.io import load_yaml, write_yaml  # noqa: E402
from fm.project import Project  # noqa: E402

SLUG = "m1_demo"
AGENT = "agent:claude-code"
HUMAN = "human:gokhan"


def banner(n, title):
    print("\n" + "=" * 78 + f"\n {n}. {title}\n" + "=" * 78, flush=True)


def fm(*args, actor=AGENT, expect=0, show=True, project=SLUG, tail=None):
    env = {**os.environ, "FM_ROOT": str(ROOT), "FM_ACTOR": actor, "PYTHONIOENCODING": "utf-8"}
    cmd = [sys.executable, "-m", "fm.cli", *(["-p", project] if project else []), *args]
    print(f"\n$ [{actor}] fm {' '.join(args)}", flush=True)
    p = subprocess.run(cmd, capture_output=True, text=True, env=env, encoding="utf-8")
    out = (p.stdout + p.stderr).rstrip()
    if show and out:
        lines = out.splitlines()
        if tail and len(lines) > tail:
            lines = ["  ..."] + lines[-tail:]
        print("\n".join("  " + ln for ln in lines))
    print(f"  -> exit {p.returncode}", flush=True)
    if expect is not None and p.returncode != expect:
        raise SystemExit(f"UNEXPECTED exit {p.returncode} (expected {expect}) for: fm {' '.join(args)}")
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", action="store_true")
    a = ap.parse_args()
    pdir = ROOT / "projects" / SLUG
    for slug in (SLUG, "m1_production_check"):
        d = ROOT / "projects" / slug
        if d.exists():
            if not a.clean:
                raise SystemExit(f"{d} exists; rerun with --clean")
            shutil.rmtree(d)
    os.environ["FM_ROOT"] = str(ROOT)
    proj = Project(ROOT, SLUG)

    # ------------------------------------------------------------------ 1
    banner(1, "fm init")
    fm("init", SLUG, "--title", "Last Signal (M1 demo)", "--sandbox", project=None)
    fm("validate")

    # ------------------------------------------------------------------ 2
    banner(2, "State transitions")
    fm("advance")                                     # IDEA -> BRIEF
    with testing.as_actor(AGENT):
        testing.produce(proj, "BRIEF")                # agent fills brief + intent canon
    print("\n  (agent wrote 00_brief/brief.yaml and canon/intent.yaml as PROPOSED)")
    fm("advance")                                     # BRIEF -> CREATIVE_DIRECTION
    fm("submit", expect=1, tail=3)                    # deliverables missing
    with testing.as_actor(AGENT):
        testing.produce(proj, "CREATIVE_DIRECTION")
    print("\n  (agent wrote CREATIVE_DIRECTION.md and canon/tone.yaml as PROPOSED)")
    fm("advance", expect=2)                           # gate G1 not approved
    fm("submit")
    fm("advance", expect=2)                           # awaiting human approval

    # ------------------------------------------------------------------ 3
    banner(3, "Approval gates — agents propose, humans decide")
    fm("approve", "G1", "--sandbox-confirm", expect=3)            # agent refused
    fm("revise", "G1", "--notes", "Make the ending's hope smaller.", "--sandbox-confirm", actor=HUMAN)
    fm("submit")
    fm("approve", "G1", "--notes", "Direction approved.", "--sandbox-confirm", actor=HUMAN)
    fm("canon", "list")
    fm("advance")

    # ------------------------------------------------------------------ 4
    banner(4, "Canon validation")
    look = proj.canon_dir / "look.yaml"
    original = look.read_text(encoding="utf-8")
    write_yaml(look, {"domain": "look", "entries": [
        {"id": "look.color.primary", "statement": "Night blue", "value": "#1B2A3A",
         "status": "LOCKED", "rationale": "cold"},                       # claims LOCKED
        {"id": "look.grain", "statement": "Heavy film grain", "status": "PROPOSED"},  # no rationale
        {"id": "look.color.accent", "statement": "Amber", "serves": ["intent.nonexistent"],
         "rationale": "warmth"},                                         # dangling intent
    ]})
    print("\n  (an agent wrote three bad canon entries into canon/look.yaml)")
    fm("validate", expect=1)
    look.write_text(original, encoding="utf-8")
    print("\n  (reverted)")
    fm("validate", "-q")

    # ------------------------------------------------------------------ 5
    banner(5, "Dependency hashing")
    print("\n  (driving the toy film through G2–G5 with simulated approvals...)", flush=True)
    testing.drive(proj, "ASSET_PREP")
    fm("status", tail=30)
    fm("hash", "canon:characters.mara.wardrobe.jacket")
    fm("deps", "artifact:character_bible")
    fm("deps", "shot:SC01_SH010")
    print("\n  Recording toy downstream products (as Blender builders will from M3):")
    for kind, deps in (("resolved", ["shot:SC01_SH010", "canon:look.color.primary"]),
                       ("blend", ["resolved:SC01_SH010"]),
                       ("render", ["blend:SC01_SH010"]),
                       ("qa", ["render:SC01_SH010"])):
        fm("record", f"{kind}:SC01_SH010", *sum((["--from", d] for d in deps), []))
    fm("record", "resolved:SC02_SH010", "--from", "shot:SC02_SH010", "--from", "canon:look.color.primary")

    # ------------------------------------------------------------------ 6
    banner(6, "fm impact with a toy change (hypothetical: nothing is modified)")
    fm("impact", "canon:characters.mara.wardrobe.jacket")
    fm("impact", "canon:look.color.primary")
    fm("plan", "--scope", "film")

    # ------------------------------------------------------------------ 7
    banner(7, "Locked decisions cannot be silently changed")
    chars = proj.canon_dir / "characters.yaml"
    original = chars.read_text(encoding="utf-8")
    data = load_yaml(chars)
    for e in data["entries"]:
        if e["id"] == "characters.mara.wardrobe.jacket":
            e["statement"] = "Dark brown waxed jacket."
            e["value"]["color"] = "#3B2A1E"
    write_yaml(chars, data)
    print("\n  (an agent edited the LOCKED jacket entry directly in canon/characters.yaml)")
    fm("validate", "-q", expect=1)
    fm("advance", expect=2, tail=4)
    chars.write_text(original, encoding="utf-8")
    print("\n  (reverted; now the legitimate route: a change request)")
    fm("change", "propose", "characters.mara.wardrobe.jacket",
       "--set", "statement=Dark brown waxed jacket.",
       "--set", "value={color: '#3B2A1E', material: waxed cotton}",
       "--reason", "Brown separates her from the blue night better than black.")
    fm("change", "approve", "CHANGE-001", "--sandbox-confirm", expect=3)   # agent refused
    fm("change", "approve", "CHANGE-001", "--notes", "Agreed.", "--sandbox-confirm", actor=HUMAN)
    fm("canon", "show", "characters.mara.wardrobe.jacket")
    fm("validate", "-q")
    print("\n  Partial production: only what the change touched needs regenerating")
    fm("plan", "--scope", "character:mara")
    fm("plan", "--scope", "scene:SC02")
    fm("advance", expect=2, tail=6)
    fm("log", "--tail", "12")

    print("\n  Same approval in a PRODUCTION project (no simulation allowed):")
    fm("init", "m1_production_check", "--title", "Production check", project=None)
    fm("authorize", "final-render", "--sandbox-confirm", actor=HUMAN, expect=3,
       project="m1_production_check")
    fm("authorize", "final-render", actor=HUMAN, expect=3, project="m1_production_check")
    shutil.rmtree(ROOT / "projects" / "m1_production_check")

    # ------------------------------------------------------------------ 8
    banner(8, "Resulting project tree")
    for path in sorted(pdir.rglob("*")):
        rel = path.relative_to(pdir)
        if any(part in ("logs",) for part in rel.parts) or path.name == ".gitkeep":
            continue
        depth = len(rel.parts) - 1
        print("  " + "    " * depth + (rel.name + "/" if path.is_dir() else rel.name))
    print("\nDemo complete.")


if __name__ == "__main__":
    main()
