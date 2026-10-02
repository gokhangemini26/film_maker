"""The OPT-IN cinematic pipeline: Cycles + denoiser profiles, HDRI + volumetric fog, compositor grade, Resolve hand-off.

Three kinds of test here, kept apart on purpose:
  * pure Python (profiles, planners, asset records, schema, resolver merge): always run;
  * last_signal guards: the locked EEVEE toon demo must validate, hash and resolve exactly as before;
  * bpy module tests (CPU Cycles, tiny frames): skipped when bpy is not installed. They ran on bpy 5.0.1, never on the pinned 5.2.1.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender"))
sys.path.insert(0, str(ROOT / "core"))

from fm import cinematic as CIN  # noqa: E402
from fm import finalrender as FR  # noqa: E402
from fm import handoff, renderprofile as RP  # noqa: E402
from fm.errors import FMError  # noqa: E402
from fm.io import hash_obj  # noqa: E402
from fm.project import Project, shot_hash  # noqa: E402
from fm.schemas import SHOT_NON_CONTENT, Atmosphere, CanonEntry, Grade, ShotSpec  # noqa: E402
from fm_blender import atmosphere as AT  # noqa: E402
from fm_blender import grade as GR  # noqa: E402
from fm_blender import render_engine as RE  # noqa: E402

HAVE_BPY = importlib.util.find_spec("bpy") is not None
bpy_only = pytest.mark.skipif(not HAVE_BPY, reason="bpy module not installed")
LAST_SIGNAL = ROOT / "projects" / "last_signal"
needs_ls = pytest.mark.skipif(not (LAST_SIGNAL / "canon" / "look.yaml").exists(), reason="Last Signal absent")

GOOD_ASSET = "file: sky_1k.hdr\nlicence: CC0-1.0\nsource_url: https://polyhaven.com/a/kloofendal_48d_partly_cloudy\nresolution: 1k\ntags: [sky, outdoor]\n"


# ------------------------------------------------------------------------------------------------ render profiles
def _prof(name):
    return yaml.safe_load((ROOT / "config" / "render_profiles.yaml").read_text())["profiles"][name]


def test_default_profiles_are_still_eevee_and_cinematic_ones_are_cycles():
    assert _prof("preview")["engine"] == "BLENDER_EEVEE" and _prof("final")["engine"] == "BLENDER_EEVEE"
    for name in ("cinematic_preview", "cinematic_final"):
        p = _prof(name)
        RP.validate_profile(p, name)
        assert p["engine"] == "CYCLES" and p["denoiser"] in RP.DENOISERS and p["device"] in RP.DEVICES
        assert p["adaptive_sampling"] is True and p["output"] == "png"
    f = _prof("cinematic_final")
    assert f["requires_authorization"] is True and f["chunk_frames"] <= 48 and f["color_depth"] == 16
    assert _prof("final")["requires_authorization"] is True and "denoiser" not in _prof("final")


def test_profile_validation_refuses_bad_values():
    for bad, msg in (({"engine": "OCTANE"}, "engine"), ({"engine": "CYCLES", "denoiser": "magic"}, "denoiser"),
                     ({"engine": "CYCLES", "device": "tpu"}, "device"), ({"engine": "CYCLES", "samples": 0}, "samples"),
                     ({"engine": "CYCLES", "color_depth": 12}, "color_depth"),
                     ({"engine": "BLENDER_EEVEE", "denoiser": "oidn"}, "only apply to engine: CYCLES")):
        with pytest.raises(FMError, match=msg):
            RP.validate_profile(bad, "x")


def test_cycles_settings_and_subprocess_env(monkeypatch, tmp_path):
    monkeypatch.delenv(RP.ENV, raising=False)
    assert RP.cycles_settings(_prof("final")) is None and RP.subprocess_env(_prof("final"), tmp_path) is None
    assert RP.subprocess_env(None, tmp_path) is None
    cs = RP.cycles_settings({"engine": "CYCLES", "samples": 8, "denoiser": "OIDN"}, samples=4)
    assert cs["samples"] == 4 and cs["denoiser"] == "oidn" and cs["adaptive_sampling"] is True and cs["device"] == "auto"
    env = RP.subprocess_env(_prof("cinematic_preview"), tmp_path)
    assert json.loads(env[RP.ENV])["engine"] == "CYCLES" and env[RP.LIBRARY_ENV] == str(tmp_path / "library")
    # an EEVEE run never inherits a stray variable
    monkeypatch.setenv(RP.ENV, '{"engine": "CYCLES"}')
    assert RP.ENV not in RP.subprocess_env(_prof("final"), tmp_path)


def test_load_profile_project_override_and_unknown(tmp_path):
    proj = SimpleNamespace(dir=tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "render.yaml").write_text(
        "profiles:\n  cinematic_final:\n    samples: 8\n    denoiser: none\n  mine:\n    engine: CYCLES\n    samples: 2\n")
    p = RP.load_profile(proj, ROOT, "cinematic_final")
    assert p["samples"] == 8 and p["denoiser"] == "none" and p["engine"] == "CYCLES" and p["requires_authorization"] is True
    assert RP.load_profile(proj, ROOT, "mine")["samples"] == 2
    with pytest.raises(FMError, match="no render profile 'nope'"):
        RP.load_profile(proj, ROOT, "nope")
    assert RP.load_profile(proj, ROOT, "final")["engine"] == "BLENDER_EEVEE"          # untouched by the override file


# ------------------------------------------------------------------------------------------------ denoiser / device planners
def test_plan_denoiser_fallback_chain():
    assert RE.plan_denoiser("oidn", "CPU", True)[0] == "oidn"
    assert RE.plan_denoiser("oidn", "CPU", False)[0] == "none"                       # oidn -> none
    assert RE.plan_denoiser("optix", "OPTIX", True)[0] == "optix"
    used, why = RE.plan_denoiser("optix", "CPU", True)
    assert used == "oidn" and "OptiX" in why                                         # optix -> oidn
    assert RE.plan_denoiser("optix", "CUDA", False)[0] == "none"                     # ... -> none
    assert RE.plan_denoiser("auto", "OPTIX", True)[0] == "optix" and RE.plan_denoiser("auto", "CPU", True)[0] == "oidn"
    assert RE.plan_denoiser("none", "OPTIX", True)[0] == "none"
    with pytest.raises(RE.RenderEngineError):
        RE.plan_denoiser("bm3d", "CPU", True)


def test_plan_device():
    assert RE.plan_device("cpu", {"OPTIX"})[0] == "CPU"
    assert RE.plan_device("auto", set())[0] == "CPU"                                 # a Windows ARM laptop: no GPU backend
    assert RE.plan_device("auto", {"CUDA", "OPTIX"})[0] == "OPTIX"
    dev, why = RE.plan_device("metal", {"CUDA"})
    assert dev == "CPU" and "no such device" in why
    assert RE.plan_device("cuda", {"CUDA", "OPTIX"})[0] == "CUDA"


def test_profile_from_env_only_for_cycles(monkeypatch):
    assert RE.profile_from_env({}) is None
    assert RE.profile_from_env({RE.ENV: '{"engine": "BLENDER_EEVEE"}'}) is None
    assert RE.profile_from_env({RE.ENV: '{"engine": "CYCLES", "samples": 3}'})["samples"] == 3
    with pytest.raises(RE.RenderEngineError):
        RE.profile_from_env({RE.ENV: "{not json"})


# ------------------------------------------------------------------------------------------------ HDRI asset records
def _lib(tmp_path, yaml_text=GOOD_ASSET, hdri="sky", with_file=True):
    d = tmp_path / "hdri" / hdri
    d.mkdir(parents=True)
    if yaml_text is not None:
        (d / "asset.yaml").write_text(yaml_text)
    if with_file:
        (d / "sky_1k.hdr").write_bytes(b"#?RADIANCE\n")
    return tmp_path


def test_hdri_asset_ok(tmp_path):
    a = AT.load_hdri_asset("sky", _lib(tmp_path))
    assert a["licence"] == "CC0-1.0" and a["file"] == "sky_1k.hdr" and a["resolution"] == "1k" and a["tags"] == ["sky", "outdoor"]
    assert a["path"].endswith("sky_1k.hdr")


@pytest.mark.parametrize("text,msg", [
    (None, "asset.yaml not found"),
    ("file: sky_1k.hdr\nsource_url: https://polyhaven.com/a/x\n", "missing licence"),
    ("file: sky_1k.hdr\nlicence: UNKNOWN\nsource_url: https://polyhaven.com/a/x\n", "UNKNOWN"),
    ("file: sky_1k.hdr\nlicence: TODO\nsource_url: https://polyhaven.com/a/x\n", "licence is 'TODO'"),
    ("file: sky_1k.hdr\nlicence: CC0-1.0\n", "missing source_url"),
    ("licence: CC0-1.0\nsource_url: https://polyhaven.com/a/x\n", "missing file"),
    ("file: sky_1k.hdr\nlicence: CC-BY-4.0\nsource_url: https://polyhaven.com/a/x\n", "Poly Haven assets are CC0"),
    ("file: ../x.hdr\nlicence: CC0-1.0\nsource_url: https://polyhaven.com/a/x\n", "plain file name"),
    ("file: sky.png\nlicence: CC0-1.0\nsource_url: https://polyhaven.com/a/x\n", "plain file name"),
])
def test_hdri_asset_refusals(tmp_path, text, msg):
    with pytest.raises(AT.AtmosphereError, match=msg):
        AT.load_hdri_asset("sky", _lib(tmp_path, text))


def test_hdri_missing_file_and_bad_checksum_and_bad_id(tmp_path):
    lib = _lib(tmp_path, with_file=False)
    with pytest.raises(AT.AtmosphereError, match="polyhaven.com"):
        AT.load_hdri_asset("sky", lib)
    assert AT.load_hdri_asset("sky", lib, require_file=False)["id"] == "sky"       # record check alone (fm validate on a clone)
    lib2 = _lib(tmp_path / "b", GOOD_ASSET + 'sha256: "' + "0" * 64 + '"\n')
    with pytest.raises(AT.AtmosphereError, match="does not match the sha256"):
        AT.load_hdri_asset("sky", lib2)
    lib3 = _lib(tmp_path / "c", GOOD_ASSET + "sha256: " + "0" * 64 + "\n")           # unquoted: YAML turns it into the number 0
    with pytest.raises(AT.AtmosphereError, match="quoted string"):
        AT.load_hdri_asset("sky", lib3)
    import hashlib
    good = hashlib.sha256(b"#?RADIANCE\n").hexdigest()
    assert AT.load_hdri_asset("sky", _lib(tmp_path / "d", GOOD_ASSET + f'sha256: "{good}"\n'))["sha256"] == good
    with pytest.raises(AT.AtmosphereError, match="invalid hdri id"):
        AT.load_hdri_asset("../etc", lib)
    with pytest.raises(AT.AtmosphereError, match="not found"):
        AT.load_hdri_asset("other", lib)


def test_simple_yaml_parser_matches_pyyaml_for_an_asset_file():
    assert AT.parse_simple_yaml(GOOD_ASSET) == yaml.safe_load(GOOD_ASSET)
    assert AT.parse_simple_yaml("tags:\n  - a\n  - b\nfile: 'x.hdr'  # c\n") == {"tags": ["a", "b"], "file": "x.hdr"}


def test_atmosphere_normalise_defaults_and_errors():
    n = AT.normalise({"hdri": {"id": "sky"}, "fog": {"density": 0.02}})
    assert n["hdri"] == {"id": "sky", "rotation_deg": 0.0, "strength": 1.0, "camera_visible": True}
    assert n["fog"]["colour"] == "#FFFFFF" and n["fog"]["bounds"] == "world" and n["fog"]["height_falloff"] == 0.0
    for bad in ({}, {"fog": {"density": 0}}, {"fog": {"density": 1, "anisotropy": 1.0}}, {"fog": {"density": 1, "colour": "red"}},
                {"fog": {"density": 1, "bounds": "box"}}, {"fog": {"density": 1, "height_falloff": -1}}):
        with pytest.raises(AT.AtmosphereError):
            AT.normalise(bad)


# ------------------------------------------------------------------------------------------------ grade plan
def test_grade_plan_order_and_validation():
    plan = GR.grade_plan({"glare": {"strength": 0.2}, "saturation": 0.9, "exposure_ev": 0.5, "view_transform": "AgX",
                          "color_balance": {"lift": [1, 1, 1.1], "gain": [1.1, 1, 0.9]}, "curves": [[0, 0], [0.5, 0.45], [1, 1]]})
    assert [s["step"] for s in plan] == ["view_transform", "exposure", "color_balance", "saturation", "curves", "glare"]
    assert plan[2]["gamma"] == [1.0, 1.0, 1.0] and plan[2]["mode"] == "lift_gamma_gain"
    cdl = GR.grade_plan({"color_balance": {"mode": "cdl", "slope": [1.1, 1, 1]}})[0]
    assert cdl["offset"] == [0.0, 0.0, 0.0] and cdl["slope"] == [1.1, 1.0, 1.0]
    for bad in ({}, {"view_transform": "Sepia"}, {"exposure_ev": 20}, {"saturation": -1}, {"curves": [[0, 0]]},
                {"curves": [[0, 0], [0, 1]]}, {"color_balance": {"gain": [9, 1, 1]}}, {"color_balance": {"mode": "x"}},
                {"glare": {"type": "star"}}):
        with pytest.raises(GR.GradeError):
            GR.grade_plan(bad)


# ------------------------------------------------------------------------------------------------ schema + hashing
def _spec(**kw):
    return ShotSpec(shot_id="SC01_SH010", scene_id="SC01", duration_s=3, **kw)


def test_blocks_need_a_rationale_on_a_shot_and_something_to_do():
    with pytest.raises(ValueError, match="atmosphere needs a rationale"):
        _spec(atmosphere={"fog": {"density": 0.01}})
    with pytest.raises(ValueError, match="grade needs a rationale"):
        _spec(grade={"exposure_ev": 0.2})
    ok = _spec(atmosphere={"fog": {"density": 0.01}, "rationale": "haze separates the planes"},
               grade={"exposure_ev": 0.2, "rationale": "lift the night a little"})
    assert ok.atmosphere.fog.density == 0.01 and ok.grade.exposure_ev == 0.2
    with pytest.raises(ValueError, match="at least one"):
        Atmosphere.model_validate({"rationale": "x"})
    with pytest.raises(ValueError, match="at least one"):
        Grade.model_validate({"rationale": "x"})
    with pytest.raises(ValueError, match="box"):
        Atmosphere.model_validate({"fog": {"density": 0.01, "bounds": "box"}})
    with pytest.raises(ValueError, match="strictly increasing"):
        Grade.model_validate({"curves": [[0, 0], [0.5, 0.5], [0.4, 0.6]]})


def test_shot_hash_ignores_unset_cinematic_fields_and_sees_set_ones():
    s = _spec()
    legacy = hash_obj({k: v for k, v in s.model_dump(mode="json", exclude=set(SHOT_NON_CONTENT)).items()
                       if k not in ("atmosphere", "grade")})
    assert shot_hash(s) == legacy                                    # exactly the hash a shot had before these fields existed
    g = _spec(grade={"saturation": 0.8, "rationale": "r"})
    assert shot_hash(g) != legacy
    assert shot_hash(_spec(grade={"saturation": 0.7, "rationale": "r"})) != shot_hash(g)


# ------------------------------------------------------------------------------------------------ canon merge (pure)
def _entry(cid, value, applies_to=()):
    return SimpleNamespace(entry=CanonEntry(id=cid, statement="s", value=value, rationale="because", applies_to=list(applies_to)),
                           path=Path("canon/look.yaml"))


def _loaded(*items):
    return SimpleNamespace(canon={i.entry.id: i for i in items})


def test_pick_canon_most_specific_wins_and_ambiguity_is_refused():
    film = _entry("look.grade", {"saturation": 0.9})
    sc02 = _entry("look.grade.sc02", {"saturation": 0.7}, ["SC02"])
    shot = _entry("look.grade.hero", {"saturation": 0.5}, ["SC02_SH020"])
    L = _loaded(film, sc02, shot)
    assert CIN.pick_canon(L, "look.grade", "SC01_SH010", "SC01")[0] == "look.grade"
    assert CIN.pick_canon(L, "look.grade", "SC02_SH010", "SC02")[0] == "look.grade.sc02"
    assert CIN.pick_canon(L, "look.grade", "SC02_SH020", "SC02")[0] == "look.grade.hero"
    assert CIN.pick_canon(_loaded(sc02), "look.grade", "SC01_SH010", "SC01") is None
    assert CIN.pick_canon(_loaded(), "look.grade", "SC01_SH010", "SC01") is None
    with pytest.raises(FMError, match="same specificity"):
        CIN.pick_canon(_loaded(film, _entry("look.grade.other", {"saturation": 1.1})), "look.grade", "SC01_SH010", "SC01")


def test_resolve_blocks_shot_overrides_canon_and_adds_refs():
    L = _loaded(_entry("look.grade", {"saturation": 0.9}), _entry("look.atmosphere", {"fog": {"density": 0.01}}))
    out, refs = CIN.resolve_blocks(L, _spec())
    assert out["grade"]["source"] == "canon:look.grade" and out["atmosphere"]["fog"]["density"] == 0.01
    assert refs == {"canon:look.grade", "canon:look.atmosphere"}
    own = _spec(grade={"saturation": 0.5, "rationale": "r"})
    out, refs = CIN.resolve_blocks(L, own)
    assert out["grade"]["source"] == "shot" and out["grade"]["saturation"] == 0.5 and refs == {"canon:look.atmosphere"}
    assert CIN.resolve_blocks(_loaded(), _spec()) == ({}, set())                       # nothing applies -> nothing added
    with pytest.raises(FMError, match="not a valid grade block"):
        CIN.resolve_blocks(_loaded(_entry("look.grade", {"saturation": 99})), _spec())


# ------------------------------------------------------------------------------------------------ last_signal is untouched
@needs_ls
def test_last_signal_validates_and_resolves_exactly_as_before():
    from fm.resolve import film_format, frame_table, resolve_shot
    from fm.validate import validate

    p = Project(ROOT, "last_signal")
    rep = validate(p)
    assert not rep.errors
    assert not [f for f in rep.findings if f.code in ("HDRI_ASSET", "CINEMATIC_SCHEMA", "CINEMATIC_AMBIGUOUS")]
    loaded = p.load()
    assert not [c for c in loaded.canon if c.startswith(("look.atmosphere", "look.grade"))]     # its canon locks no such block
    fmt = film_format(loaded)
    table = frame_table(loaded, fmt["fps"])
    for sid, item in loaded.shots.items():
        assert item.spec.atmosphere is None and item.spec.grade is None
        legacy = hash_obj({k: v for k, v in item.spec.model_dump(mode="json", exclude=set(SHOT_NON_CONTENT)).items()
                           if k not in ("atmosphere", "grade")})
        assert shot_hash(item.spec) == legacy == item.hash, sid                     # no shot node can go stale
        data, _refs = resolve_shot(p, loaded, sid, table, fmt)
        assert "atmosphere" not in data and "grade" not in data
        on_disk = json.loads((p.dir / "09_resolved" / f"{sid}.json").read_text(encoding="utf-8"))
        assert data == on_disk, sid                                                 # identical resolved output (so identical hash)


def test_default_profiles_pass_no_environment_to_blender(monkeypatch):
    """`fm blender preview/frames/playblast` without --profile, and with an EEVEE profile, spawn Blender exactly as before."""
    from fm import blenderrun as BR
    monkeypatch.delenv(RP.ENV, raising=False)
    assert BR._profile_env(SimpleNamespace(dir=ROOT / "projects" / "last_signal"), ROOT, None) == (None, None)
    prof, env = BR._profile_env(SimpleNamespace(dir=ROOT / "projects" / "last_signal"), ROOT, "final")
    assert prof["engine"] == "BLENDER_EEVEE" and env is None
    prof, env = BR._profile_env(SimpleNamespace(dir=ROOT / "projects" / "last_signal"), ROOT, "cinematic_preview", samples=2)
    assert json.loads(env[RP.ENV])["samples"] == 2


# ------------------------------------------------------------------------------------------------ a real resolve + validate
from .test_final_render import _authorize, _calls, _template, prod  # noqa: E402,F401  (fixtures: a resolved sandbox film)


def _edit_yaml(path, fn):
    data = yaml.safe_load(path.read_text())
    fn(data)
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def test_resolver_validate_and_handoff_on_a_sandbox_film(prod, monkeypatch):
    from fm.ops import refresh
    from fm.resolve import resolve
    from fm.validate import validate

    shots_dir = prod.dir / "08_shots"
    sid1, sid2 = "SC01_SH010", "SC02_SH010"
    _edit_yaml(shots_dir / f"{sid1}.shot.yaml", lambda d: d.update(
        atmosphere={"hdri": {"id": "kloof", "rotation_deg": 30, "strength": 0.9}, "fog": {"density": 0.01, "height_falloff": 0.3},
                    "rationale": "dusk sky and a haze that separates the planes"}))
    canon_p = prod.dir / "canon" / "look.yaml"
    _edit_yaml(canon_p, lambda d: d["entries"].extend([
        {"id": "look.grade", "statement": "film-wide grade", "value": {"saturation": 0.9}, "rationale": "calm the palette", "tag": "DECISION"},
        {"id": "look.grade.sc02", "statement": "SC02 grade", "value": {"exposure_ev": 0.4}, "rationale": "brighter room",
         "applies_to": ["SC02"], "tag": "DECISION"}]))
    # no library/hdri/kloof yet: validate names the problem as an ERROR
    rep = validate(prod)
    bad = [f for f in rep.findings if f.code == "HDRI_ASSET"]
    assert bad and bad[0].level == "ERROR" and "asset.yaml not found" in bad[0].message
    lib = prod.repo / "library" / "hdri" / "kloof"
    lib.mkdir(parents=True)
    (lib / "asset.yaml").write_text(GOOD_ASSET)
    rep = validate(prod)
    warn = [f for f in rep.findings if f.code == "HDRI_ASSET"]
    assert warn and warn[0].level == "WARN" and "not found" in warn[0].message                # record fine, binary not here
    (lib / "sky_1k.hdr").write_bytes(b"#?RADIANCE\n")
    assert not [f for f in validate(prod).findings if f.code == "HDRI_ASSET"]

    resolve(prod)
    rd = prod.dir / "09_resolved"
    a = json.loads((rd / f"{sid1}.json").read_text())
    assert a["atmosphere"]["hdri"]["id"] == "kloof" and a["atmosphere"]["source"] == "shot"
    assert a["grade"] == {"saturation": 0.9, "source": "canon:look.grade"}
    b = json.loads((rd / f"{sid2}.json").read_text())
    assert b["grade"] == {"exposure_ev": 0.4, "source": "canon:look.grade.sc02"} and "atmosphere" not in b
    derived = prod.load().derived[f"resolved:{sid2}"]
    assert "canon:look.grade.sc02" in {d.ref for d in derived.derived_from}                   # a grade change makes the shot stale

    out = handoff.grade_handoff(prod)
    assert out["shots_with_grade"] >= 2 and set(out["files"]) == {"GRADE_SPEC.yaml", "grade_spec.json", "README_RESOLVE.md"}
    spec = yaml.safe_load((Path(out["dir"]) / "GRADE_SPEC.yaml").read_text())
    assert spec["schema"] == "fm.grade_handoff/1" and spec["shots"][sid2]["grade"]["exposure_ev"] == 0.4
    assert spec["shots"][sid1]["atmosphere"]["hdri"]["id"] == "kloof" and "rationale" not in spec["shots"][sid1]["atmosphere"]
    readme = (Path(out["dir"]) / "README_RESOLVE.md").read_text()
    assert "not automated" in readme and "starting point" in readme


# ------------------------------------------------------------------------------------------------ final render honours the profile
def _spy_run(monkeypatch):
    seen = []
    real = subprocess.run

    def spy(cmd, **kw):
        seen.append(kw.get("env"))
        return real(cmd, **kw)

    monkeypatch.setattr(FR.subprocess, "run", spy)
    return seen


def test_final_default_profile_is_unchanged_and_cinematic_profile_selects_cycles(prod, monkeypatch):
    monkeypatch.delenv(RP.ENV, raising=False)
    seen = _spy_run(monkeypatch)
    _authorize(prod)
    FR.final(prod, prod.repo, width=64)
    assert seen and all(e is None for e in seen)                                        # EEVEE: Blender is spawned as before
    m = json.loads((prod.dir / FR.MANIFEST).read_text())
    assert "cycles" not in m["shots"]["SC01_SH010"]["profile"]                           # the old fingerprint, byte for byte

    seen.clear()
    r = FR.final(prod, prod.repo, width=64, profile="cinematic_final", samples=6, resume=True)
    assert r["failed_chunks"] == [] and seen and all(e and json.loads(e[RP.ENV])["samples"] == 6 for e in seen)
    e0 = json.loads((prod.dir / FR.MANIFEST).read_text())["shots"]["SC01_SH010"]
    cy = e0["profile"]["cycles"]
    assert e0["profile"]["engine"] == "CYCLES" and cy["denoiser"] == "auto" and cy["color_depth"] == 16 and cy["samples"] == 6
    assert e0["complete"] is True and e0["samples"] == 6
    # the engine change re-rendered the shot instead of mixing settings
    assert e0["profile"]["engine"] != "BLENDER_EEVEE"


def test_final_cinematic_profile_still_needs_the_humans_authorization(prod):
    with pytest.raises(FMError, match="authorization"):
        FR.final(prod, prod.repo, width=64, profile="cinematic_final")
    assert _calls(prod) == []


def test_final_with_unknown_profile_is_refused(prod):
    _authorize(prod)
    with pytest.raises(FMError, match="no render profile"):
        FR.final(prod, prod.repo, width=64, profile="cinematic_finl")


# ------------------------------------------------------------------------------------------------ bpy (CPU, tiny)
def _cycles_env(monkeypatch, **over):
    prof = {"engine": "CYCLES", "samples": 2, "adaptive_sampling": True, "adaptive_threshold": 0.1, "denoiser": "oidn",
            "device": "auto", "motion_blur": False, **over}
    monkeypatch.setenv(RE.ENV, json.dumps(prof))


@bpy_only
def test_setup_render_is_eevee_toon_without_a_profile_and_cycles_pbr_with_one(monkeypatch):
    import bpy
    from fm_blender import preview as P
    from fm_blender import util as U
    film = {"format": {"aspect_ratio": 16 / 9, "fps": 24}}
    monkeypatch.delenv(RE.ENV, raising=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    U.SHADING[0] = "toon"
    P.setup_render(film, 64)
    sc = bpy.context.scene
    assert sc.render.engine.startswith("BLENDER_EEVEE") and U.SHADING[0] == "toon" and sc.view_settings.view_transform == "Standard"
    assert U.toon("#336699").node_tree.nodes.get("Shader to RGB") is not None or any(
        n.bl_idname == "ShaderNodeShaderToRGB" for n in U.toon("#336699").node_tree.nodes)
    _cycles_env(monkeypatch)
    try:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        P.setup_render(film, 64)
        sc = bpy.context.scene
        assert sc.render.engine == "CYCLES" and bpy.context.scene.cycles.samples == 2 and U.SHADING[0] == "pbr"
        assert sc.view_settings.view_transform == "Standard"                          # still colour-exact unless a grade says otherwise
        m = U.toon("#336699")
        assert m.name.endswith(".pbr") and not any(n.bl_idname == "ShaderNodeShaderToRGB" for n in m.node_tree.nodes)
    finally:
        U.SHADING[0] = "toon"


@bpy_only
def test_configure_cycles_cpu_denoiser_and_log(monkeypatch):
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    lines = []
    rep = RE.configure(bpy.context.scene, {"engine": "CYCLES", "samples": 3, "denoiser": "optix", "device": "optix", "color_depth": 16,
                                           "max_bounces": 4}, log=lines.append)
    sc = bpy.context.scene
    assert sc.render.engine == "CYCLES" and sc.cycles.device == "CPU" and sc.cycles.samples == 3 and sc.cycles.max_bounces == 4
    assert rep["denoiser_used"] in ("oidn", "none") and rep["denoiser_used"] != "optix"      # no NVIDIA device in CI
    assert sc.cycles.use_denoising is (rep["denoiser_used"] == "oidn")
    assert any(l.startswith("FM_DENOISER requested=optix used=") for l in lines)
    assert sc.render.image_settings.color_depth == "16"
    RE.configure(sc, {"engine": "CYCLES", "denoiser": "none"}, log=lambda *_: None)
    assert sc.cycles.use_denoising is False


@bpy_only
def test_hdri_and_fog_nodes(monkeypatch, tmp_path):
    import bpy
    lib = _lib(tmp_path)
    img = bpy.data.images.new("t", 8, 4, float_buffer=True)
    img.filepath_raw = str(lib / "hdri" / "sky" / "sky_1k.hdr")
    img.file_format = "HDR"
    img.save()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    w = bpy.data.worlds.new("fm.world")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    lines = []
    rep = AT.apply_hdri(sc, "sky", 90, 0.7, root=lib, log=lines.append)
    nt = w.node_tree
    assert rep["licence"] == "CC0-1.0" and nt.nodes["Background"].inputs[1].default_value == pytest.approx(0.7)
    env = nt.nodes["fm_hdri_env"]
    assert env.image is not None and nt.nodes["Background"].inputs[0].links[0].from_node == env
    assert nt.nodes["fm_hdri_mapping"].inputs["Rotation"].default_value[2] == pytest.approx(1.5707963, rel=1e-4)
    assert lines and lines[0].startswith("FM_HDRI ") and "licence=CC0-1.0" in lines[0]
    AT.apply_hdri(sc, "sky", 0, 1.0, camera_visible=False, root=lib, log=lambda *_: None)    # rebuild in place, no node pile-up
    assert len([n for n in nt.nodes if n.name.startswith("fm_hdri_env")]) == 1 and "fm_hdri_mix" in nt.nodes
    AT.apply_volumetric_fog(sc, 0.02, 0.3, 0.2, "#CCDDFF", log=lambda *_: None)
    out = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputWorld")
    assert out.inputs["Volume"].links[0].from_node.name == "fm_fog_scatter" and "fm_fog_exp" in nt.nodes
    assert nt.nodes["fm_fog_scatter"].inputs["Anisotropy"].default_value == pytest.approx(0.3)
    AT.apply_volumetric_fog(sc, 0.02, log=lambda *_: None)                                    # uniform: no height maths
    assert "fm_fog_exp" not in nt.nodes
    AT.apply_volumetric_fog(sc, 0.05, bounds="box", box={"center": [0, 0, 1], "size": [4, 4, 2]}, log=lambda *_: None)
    box = bpy.data.objects["fm_fog_box"]
    assert box.get("fm_shot") and box.get("fm_owner") == "fm_blender" and tuple(box.location) == (0, 0, 1)
    with pytest.raises(AT.AtmosphereError, match="asset.yaml not found"):
        AT.apply_hdri(sc, "missing", root=lib)


@bpy_only
def test_hooks_are_inert_without_a_cycles_profile_and_a_spec(monkeypatch):
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    monkeypatch.delenv(RE.ENV, raising=False)
    lines = []
    shot = {"shot_id": "SC01_SH010", "atmosphere": {"fog": {"density": 0.01}}, "grade": {"saturation": 0.8}}
    assert AT.apply_for_shot(sc, shot, lines.append) is None and GR.apply_for_shot(sc, shot, lines.append) is None
    assert sc.world is None and getattr(sc, "compositing_node_group", None) is None             # nothing was built
    assert len(lines) == 2 and all("skipped" in l for l in lines)
    _cycles_env(monkeypatch)
    assert AT.apply_for_shot(sc, {"shot_id": "x"}, lines.append) is None and GR.apply_for_shot(sc, {"shot_id": "x"}, lines.append) is None
    assert sc.world is None


@bpy_only
def test_grade_changes_pixels_and_can_be_replaced_and_cleared(monkeypatch, tmp_path):
    import bpy
    _cycles_env(monkeypatch, denoiser="none", samples=1)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    RE.apply_from_env(sc, lambda *_: None)
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 16, 16, 100
    sc.render.image_settings.color_depth = "8"
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.2, 0.3, 0.4, 1)

    def shoot(name):
        sc.render.filepath = str(tmp_path / name)
        bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(sc.render.filepath)
        px = list(im.pixels)
        bpy.data.images.remove(im)
        return [sum(px[i::4]) / (len(px) // 4) for i in range(3)]

    plain = shoot("a.png")
    GR.apply_grade(sc, {"exposure_ev": 1.0, "color_balance": {"gain": [1.2, 1.0, 0.8]}, "saturation": 0.5,
                        "curves": [[0, 0], [0.5, 0.4], [1, 1]]}, log=lambda *_: None)
    graded = shoot("b.png")
    assert max(abs(g - p) for g, p in zip(graded, plain)) > 0.05
    ng = sc.compositing_node_group
    assert [n.name for n in ng.nodes if n.name.startswith("fm_grade_")] and ng["fm_grade_upstream"].endswith("|Image")
    GR.apply_grade(sc, {"exposure_ev": 1.0}, log=lambda *_: None)                              # replaces, never piles up
    assert [n.name for n in ng.nodes if n.name.startswith("fm_grade_")].count("fm_grade_exposure") == 1
    assert "fm_grade_saturation" not in ng.nodes
    assert GR.clear_grade(sc) is True and GR.clear_grade(sc) is False
    back = shoot("c.png")
    assert max(abs(g - p) for g, p in zip(back, plain)) < 0.02
    with pytest.raises(GR.GradeError, match="no look"):
        GR.apply_grade(sc, {"view_transform": "AgX", "look": "Does Not Exist"}, log=lambda *_: None)


@bpy_only
def test_grade_splices_in_front_of_an_existing_final_glare(monkeypatch):
    import bpy
    from fm_blender import finish as FN
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    FN.apply_glare(bpy, sc, FN.glare_params({"look.style.glow": {"max_radius_pct_frame_width": 1.5}}, 64))
    GR.apply_grade(sc, {"saturation": 0.8}, log=lambda *_: None)
    ng = sc.compositing_node_group
    out = next(n for n in ng.nodes if n.bl_idname == "NodeGroupOutput")
    assert out.inputs[0].links[0].from_node.name == "fm_grade_saturation"
    assert ng.nodes["fm_grade_saturation"].inputs["Image"].links[0].from_node.bl_idname in ("ShaderNodeMix", "CompositorNodeMixRGB")
    assert GR.clear_grade(sc) and out.inputs[0].links[0].from_node.bl_idname in ("ShaderNodeMix", "CompositorNodeMixRGB")
    os.environ.pop(RE.ENV, None)
