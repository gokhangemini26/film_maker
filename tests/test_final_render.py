"""F3: `fm blender final` and `fm qa final` (no real Blender: a fake frame renderer stands in for the subprocess)."""
import json
import shutil
import sys
import textwrap
from pathlib import Path

import pytest
from click.testing import CliRunner

from fm import finalrender as FR
from fm import ops, testing
from fm.cli import cli
from fm.errors import FMError
from fm.project import resolve_project
from fm.resolve import resolve

REPO = Path(__file__).resolve().parents[1]

N = 4   # frames per shot in these tests

FAKE = textwrap.dedent('''
    import os, sys
    from PIL import Image
    out, sid, width, height, spec, log = sys.argv[1:7]
    fr = []
    for item in spec.split(","):
        a, _, b = item.partition("-")
        fr += list(range(int(a), int(b or a) + 1))
    with open(log, "a") as fh:
        fh.write(sid + " " + spec + "\\n")
    os.makedirs(os.path.join(out, sid), exist_ok=True)
    for f in fr:
        im = Image.new("RGB", (int(width), int(height)), (40 + f * 7 % 90, 90, 140))
        im.putpixel((0, 0), (255, 255, 255))
        im.save(os.path.join(out, sid, "%04d.png" % f))
    print("FM_OK", sid, len(fr))
''')


class _Info:
    version = "5.2.0"


@pytest.fixture(scope="module")
def _template(tmp_path_factory):
    """Built once: a resolved 3-shot sandbox film shrunk to N frames per shot (driving to STORYBOARD takes ~8 s)."""
    mp = pytest.MonkeyPatch()
    root = tmp_path_factory.mktemp("tpl") / "film_maker"
    shutil.copytree(REPO / "config", root / "config")
    shutil.copytree(REPO / "templates", root / "templates")
    (root / "projects").mkdir()
    mp.setenv("FM_ROOT", str(root))
    mp.setenv("FM_ACTOR", "agent:test")
    mp.setenv("FM_FIXED_TIME", "2026-01-01T00:00:00Z")
    mp.delenv("FM_PROJECT", raising=False)
    mp.chdir(root)
    try:
        p = ops.init_project(root, "last_signal", "Last Signal", sandbox=True)
        testing.drive(p, "STORYBOARD")
        with testing.as_actor(testing.AGENT):
            testing.produce(p, "STORYBOARD")
            testing.stamp_all(p)
        resolve(p)
        rd = p.dir / "09_resolved"
        film = json.loads((rd / "film.json").read_text())
        for i, k in enumerate(sorted(film["shots"])):
            film["shots"][k].update(frames=N, start=i * N)
        film["total_frames"] = N * len(film["shots"])
        (rd / "film.json").write_text(json.dumps(film))
        for k in film["shots"]:
            sh = json.loads((rd / f"{k}.json").read_text())
            sh["frames"].update(count=N, end=N - 1)
            sh["motion"] = {"fake": 1}
            (rd / f"{k}.json").write_text(json.dumps(sh))
        from fm.ops import refresh
        refresh(p)
    finally:
        mp.undo()
    return root


@pytest.fixture
def prod(_template, tmp_path, monkeypatch):
    """A private copy of the template project, a fake Blender and a call log."""
    root = tmp_path / "film_maker"
    shutil.copytree(_template, root)
    monkeypatch.setenv("FM_ROOT", str(root))
    monkeypatch.setenv("FM_ACTOR", "agent:test")
    monkeypatch.setenv("FM_FIXED_TIME", "2026-01-01T00:00:00Z")
    monkeypatch.delenv("FM_PROJECT", raising=False)
    monkeypatch.chdir(root)
    sandbox = resolve_project(root, "last_signal")
    monkeypatch.setattr(FR, "resolve", lambda *a, **k: None)        # keep the shrunk files
    monkeypatch.setattr(FR, "require_blender", lambda repo: _Info())
    script = tmp_path / "fake_frames.py"
    script.write_text(FAKE)
    calls = tmp_path / "calls.log"

    sandbox.final_flags = []

    def fake_cmd(repo, *, draft, resolved, out, sid, width, spec, stamp, samples, fast, resume, final=False):
        sandbox.final_flags.append(final)
        h = int(round(width / (16 / 9)))
        return [sys.executable, str(script), str(out), sid, str(width), str(h), spec, str(calls)], \
            ("bpy 5.0.1 (DRAFT, not the pinned series)" if draft else "blender 5.2.0")

    monkeypatch.setattr(FR, "_frame_cmd", fake_cmd)
    sandbox.fake_calls = calls
    return sandbox


def _authorize(p, scope="film"):
    with testing.as_actor(testing.HUMAN):
        ops.authorize(p, "final-render", scope, sandbox_confirm=True)


def _calls(p):
    f = p.fake_calls
    return f.read_text().splitlines() if f.exists() else []


def _manifest(p):
    return json.loads((p.dir / FR.MANIFEST).read_text())


# ------------------------------------------------------------------------------------------------ refusals
def test_refuses_without_authorization(prod):
    with pytest.raises(FMError, match="authorization"):
        FR.final(prod, prod.repo, width=64)
    assert _calls(prod) == []
    assert not (prod.dir / "11_render" / "final").exists()


def test_refuses_when_authorization_scope_does_not_cover(prod):
    ids = sorted(json.loads((prod.dir / "09_resolved" / "film.json").read_text())["shots"])
    _authorize(prod, f"shot:{ids[0]}")
    with pytest.raises(FMError, match="does not cover"):
        FR.final(prod, prod.repo, width=64)
    assert _calls(prod) == []
    FR.final(prod, prod.repo, scope=f"shot:{ids[0]}", width=64)     # the covered shot is fine
    assert ids[0] in _manifest(prod)["shots"] and ids[1] not in _manifest(prod)["shots"]


def test_cli_refuses_and_never_authorizes(prod):
    r = CliRunner().invoke(cli, ["blender", "final", "--width", "64"])
    assert isinstance(r.exception, FMError) and "fm authorize final-render" in str(r.exception)
    assert ops.load_state(prod).authorizations == []


def test_profile_output_must_be_png(prod):
    _authorize(prod)
    (prod.dir / "config").mkdir(exist_ok=True)
    (prod.dir / "config" / "render.yaml").write_text("profiles:\n  final:\n    output: exr\n")
    with pytest.raises(FMError, match="PNG"):
        FR.final(prod, prod.repo, width=64)


def test_shipped_final_profile_is_png(prod):
    assert FR.load_profile(prod, prod.repo)["output"] == "png"
    assert FR.load_profile(prod, prod.repo)["requires_authorization"] is True


def test_shot_without_motion_is_refused(prod):
    _authorize(prod)
    sid = sorted(json.loads((prod.dir / "09_resolved" / "film.json").read_text())["shots"])[0]
    p = prod.dir / "09_resolved" / f"{sid}.json"
    s = json.loads(p.read_text())
    s["motion"] = None
    p.write_text(json.dumps(s))
    with pytest.raises(FMError, match="no motion"):
        FR.final(prod, prod.repo, width=64)


# ------------------------------------------------------------------------------------------------ render, chunks, manifest
def test_render_chunks_manifest_and_derived(prod):
    _authorize(prod)
    r = FR.final(prod, prod.repo, width=64, chunk_frames=3, samples=8)
    assert r["failed_chunks"] == [] and len(r["complete"]) == 3 and r["pinned"] is True
    assert len(_calls(prod)) == 6                       # 4 frames at 3 per process: 2 chunks per shot
    assert sorted(set(c.split()[1] for c in _calls(prod))) == ["0-2", "3"]
    m = _manifest(prod)
    for sid, e in m["shots"].items():
        assert e["frames"] == N and e["complete"] and e["blender"] == "blender 5.2.0" and e["route"] == "exe"
        assert e["samples"] == 8 and e["profile"]["output"] == "png" and len(e["frame_sha256"]) == N
        assert sorted(p.name for p in (prod.dir / "11_render" / "final" / sid).iterdir()) == [f"{i:04d}.png" for i in range(N)]
    assert m["authorization"]["what"] == "final-render"
    d = prod.load().derived
    assert "render:final" in d and all(f"render:final_{s}" in d for s in m["shots"])


def test_scope_scene_and_frames_range(prod):
    _authorize(prod)
    FR.final(prod, prod.repo, scope="scene:SC01", width=64)
    assert set(_manifest(prod)["shots"]) == {"SC01_SH010", "SC01_SH020"}
    with pytest.raises(FMError, match="one shot"):
        FR.final(prod, prod.repo, scope="scene:SC01", width=64, frames="1-2")
    before = len(_calls(prod))
    FR.final(prod, prod.repo, scope="shot:SC01_SH010", width=64, frames="1-2")
    assert _calls(prod)[before:] == ["SC01_SH010 1-2"]
    assert _manifest(prod)["shots"]["SC01_SH010"]["complete"] is True


def test_resume_skips_valid_frames_and_redoes_bad_ones(prod):
    _authorize(prod)
    FR.final(prod, prod.repo, width=64)
    d = prod.dir / "11_render" / "final" / "SC01_SH010"
    (d / "0001.png").unlink()                                   # missing
    (d / "0002.png").write_bytes((d / "0002.png").read_bytes()[:40])   # truncated by a kill
    before = len(_calls(prod))
    r = FR.final(prod, prod.repo, width=64, resume=True)
    assert _calls(prod)[before:] == ["SC01_SH010 1-2"]          # nothing else was rendered
    assert r["frames_kept"]["SC01_SH010"] == 2 and r["frames_kept"]["SC02_SH010"] == N
    assert FR.png_info(d / "0002.png") == (64, 36) and _manifest(prod)["shots"]["SC01_SH010"]["complete"]


def test_resume_with_other_settings_rerenders_the_shot(prod):
    _authorize(prod)
    FR.final(prod, prod.repo, width=64, samples=8)
    before = len(_calls(prod))
    FR.final(prod, prod.repo, width=64, samples=16, resume=True)
    assert len(_calls(prod)) - before == 3                       # one whole-shot chunk each, nothing reused
    assert _manifest(prod)["shots"]["SC01_SH010"]["samples"] == 16
    with pytest.raises(FMError, match="other settings"):
        FR.final(prod, prod.repo, scope="shot:SC01_SH010", width=64, samples=32, frames="1-2", resume=True)


def test_failed_chunk_is_reported_and_resumable(prod, monkeypatch):
    _authorize(prod)
    real = FR._frame_cmd

    def flaky(repo, **kw):
        cmd, v = real(repo, **kw)
        if kw["sid"] == "SC02_SH010":
            cmd = [sys.executable, "-c", "print('boom')"]
        return cmd, v

    monkeypatch.setattr(FR, "_frame_cmd", flaky)
    r = FR.final(prod, prod.repo, width=64)
    assert r["failed_chunks"] == ["SC02_SH010:0-3"] and "SC02_SH010" in r["incomplete"]
    assert _manifest(prod)["shots"]["SC02_SH010"]["complete"] is False
    monkeypatch.setattr(FR, "_frame_cmd", real)
    r = FR.final(prod, prod.repo, width=64, resume=True)
    assert r["failed_chunks"] == [] and r["incomplete"] == {} and r["frames_kept"]["SC01_SH010"] == N


def test_cloud_route_is_recorded_unpinned(prod):
    _authorize(prod)
    FR.final(prod, prod.repo, width=64, route="cloud")
    e = _manifest(prod)["shots"]["SC01_SH010"]
    assert e["pinned"] is False and e["route"] == "cloud" and "DRAFT" in e["blender"]
    with pytest.raises(FMError, match="route"):
        FR.final(prod, prod.repo, width=64, route="farm")


# ------------------------------------------------------------------------------------------------ qa final
def _rendered(prod, **kw):
    _authorize(prod)
    FR.final(prod, prod.repo, width=64, **kw)
    return prod


def _findings(rep, shot=None):
    return [(r["shot"], s, m) for r in rep["rows"] if shot in (None, r["shot"]) for s, m in r["findings"]]


def test_qa_final_passes_and_writes_the_g8_report(prod):
    _rendered(prod)
    rep = FR.qa_final(prod, allow_reduced=True)
    assert rep["summary"]["fail"] == 0 and rep["summary"]["frames_found"] == rep["summary"]["frames_expected"] == 3 * N
    assert json.loads((prod.dir / "qa" / "final_frames_report.json").read_text())["summary"]["fail"] == 0
    assert "qa:final" in prod.load().derived


def test_qa_final_reduced_width_fails_unless_allowed(prod):
    _rendered(prod)
    rep = FR.qa_final(prod)
    assert any("below the film's 1920" in m for _, s, m in _findings(rep) if s == "FAIL")


def test_qa_final_without_a_manifest_or_frames_fails(prod):
    rep = FR.qa_final(prod)
    assert rep["summary"]["fail"] >= 3 and any("MANIFEST.json missing" in m for _, _, m in _findings(rep, "FILM"))


def test_qa_final_detects_missing_extra_truncated_and_hash_mismatch(prod):
    _rendered(prod)
    root = prod.dir / "11_render" / "final"
    (root / "SC01_SH010" / "0003.png").unlink()                                     # count
    (root / "SC01_SH020" / "0001.png").write_bytes((root / "SC01_SH020" / "0001.png").read_bytes()[:50])   # truncated
    from PIL import Image
    Image.new("RGB", (64, 36), (200, 10, 10)).save(root / "SC02_SH010" / "0002.png")   # valid PNG, other content
    (root / "SC02_SH010" / "0009.png").write_bytes(b"x")                              # extra file breaks `fm post assemble`
    rep = FR.qa_final(prod, allow_reduced=True)
    text = " | ".join(m for _, s, m in _findings(rep) if s == "FAIL")
    assert "3 frames, expected 4; missing 0003.png" in text
    assert "corrupt or truncated frame(s): 1" in text
    assert "do not match their MANIFEST hash: 2" in text
    assert "unexpected file(s)" in text
    assert rep["summary"]["fail"] == 4       # the three shots and the FILM row (frame total)


def test_qa_final_wrong_dimensions(prod):
    _rendered(prod)
    from PIL import Image
    Image.new("RGB", (80, 36), (90, 90, 90)).save(prod.dir / "11_render" / "final" / "SC01_SH010" / "0000.png")
    text = " | ".join(m for _, s, m in _findings(FR.qa_final(prod, allow_reduced=True)) if s == "FAIL")
    assert "differ in size from the manifest: 0:80x36" in text


def test_qa_final_black_frames(prod):
    _rendered(prod)
    from PIL import Image
    d = prod.dir / "11_render" / "final"
    Image.new("RGB", (64, 36), (0, 0, 0)).save(d / "SC01_SH010" / "0002.png")      # interior glitch
    Image.new("RGB", (64, 36), (0, 0, 0)).save(d / "SC02_SH010" / "0003.png")      # fade-out at the tail: WARN
    m = _manifest(prod)
    from fm.finalrender import _sha
    for sid, f in (("SC01_SH010", "0002.png"), ("SC02_SH010", "0003.png")):
        m["shots"][sid]["frame_sha256"][f] = _sha(d / sid / f)       # so only the black check can object
    (d / "MANIFEST.json").write_text(json.dumps(m))
    rep = FR.qa_final(prod, allow_reduced=True)
    assert any(s == "FAIL" and "black frame(s) 2-2" in m for sh, s, m in _findings(rep, "SC01_SH010"))
    assert any(s == "WARN" and "black frames 3-3" in m for sh, s, m in _findings(rep, "SC02_SH010"))
    assert not any(s == "FAIL" for _, s, _ in _findings(rep, "SC02_SH010"))


def test_qa_final_rejects_unpinned_and_stale_frames(prod):
    _authorize(prod)
    FR.final(prod, prod.repo, width=64, route="cloud")
    assert any("not rendered with the pinned Blender" in m for _, s, m in _findings(FR.qa_final(prod, allow_reduced=True)) if s == "FAIL")
    FR.final(prod, prod.repo, width=64)
    assert FR.qa_final(prod, allow_reduced=True)["summary"]["fail"] == 0
    ops.record_derived(prod, "resolved:SC01_SH010", ["shot:SC01_SH010"], content="re-resolved after a change")   # what `fm resolve` does
    assert any("stale" in m for _, sev, m in _findings(FR.qa_final(prod, allow_reduced=True), "SC01_SH010") if sev == "FAIL")


def test_g8_contract_reads_the_final_report(prod):
    from fm.phases import CONTRACTS
    loaded = prod.load
    _rendered(prod)
    c = CONTRACTS["FINAL_RENDER"]
    assert (prod.dir / FR.MANIFEST).exists()
    FR.qa_final(prod)                                    # reduced width -> FAIL
    probs = ops._contract_extras(prod, c, loaded())
    assert any("final_frames_report.json reports" in p for p in probs) and not any("authorization" in p for p in probs)
    FR.qa_final(prod, allow_reduced=True)
    probs = ops._contract_extras(prod, c, loaded())
    assert probs == []


def test_cli_qa_final_exit_codes(prod):
    _rendered(prod)
    r = CliRunner().invoke(cli, ["qa", "final"])
    assert r.exit_code == 1 and "below the film's 1920" in r.output
    r = CliRunner().invoke(cli, ["qa", "final", "--allow-reduced"])
    assert r.exit_code == 0 and "0 FAIL" in r.output


def test_ranges_and_png_info(tmp_path):
    assert FR._ranges([0, 1, 2, 3, 4, 7, 9, 10], 3) == [(0, 2), (3, 4), (7, 7), (9, 10)]
    assert FR._spec(5, 5) == "5" and FR._spec(5, 9) == "5-9"
    from PIL import Image
    p = tmp_path / "a.png"
    Image.new("RGB", (70, 40)).save(p)
    assert FR.png_info(p) == (70, 40)
    p.write_bytes(p.read_bytes()[:-3])
    assert FR.png_info(p) is None and FR.png_info(tmp_path / "none.png") is None


GLOW = {"glow_sources": "emissives_only", "max_radius_pct_frame_width": 1.5, "streaks": False, "star_glare": False,
        "ghosts": False, "bokeh_discs": False, "implementation": "compositor_glare_bloom_on_emission_pass"}


def _with_glow(monkeypatch, **over):
    real = FR._read_film

    def read(project):
        film = real(project)
        film.setdefault("canon", {})["look.style.glow"] = {**GLOW, **over}
        return film

    monkeypatch.setattr(FR, "_read_film", read)


def test_final_command_asks_the_builder_for_the_glare_and_records_it(prod, monkeypatch):
    _authorize(prod)
    _with_glow(monkeypatch)
    r = FR.final(prod, prod.repo, width=64)
    assert r["failed_chunks"] == [] and prod.final_flags and all(prod.final_flags)      # every chunk is a final-profile render
    g = _manifest(prod)["shots"]["SC01_SH010"]["profile"]["glare"]
    assert g["source"] == "look.style.glow" and g["size"] == 0.015 and g["type"] == "BLOOM"
    assert g["max_radius_px"] == round(0.015 * 64, 2)


def test_changed_glow_canon_never_mixes_settings_in_one_shot(prod, monkeypatch):
    _authorize(prod)
    _with_glow(monkeypatch)
    FR.final(prod, prod.repo, width=64, scope="shot:SC01_SH010")
    _with_glow(monkeypatch, max_radius_pct_frame_width=1.0)
    with pytest.raises(FMError, match="other settings"):
        FR.final(prod, prod.repo, width=64, scope="shot:SC01_SH010", frames="1-2", resume=True)


def test_glow_canon_the_builder_cannot_honour_refuses_before_rendering(prod, monkeypatch):
    _authorize(prod)
    _with_glow(monkeypatch, streaks=True)
    with pytest.raises(FMError, match="streaks"):
        FR.final(prod, prod.repo, width=64)
    assert prod.final_flags == [] and not (prod.dir / "11_render" / "final").exists()


def test_film_without_glow_canon_renders_without_glare(prod):
    _authorize(prod)
    FR.final(prod, prod.repo, width=64, scope="shot:SC01_SH010")
    assert _manifest(prod)["shots"]["SC01_SH010"]["profile"]["glare"] is None
