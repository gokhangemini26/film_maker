"""Final render (M6 step F3): `fm blender final` and `fm qa final`.

`final()` renders every frame of the shots in scope to ``11_render/final/<SHOT>/NNNN.png`` (shot-local, 0-based,
PNG because `fm post assemble` reads PNG), one Blender process per chunk of at most `chunk_frames` frames, and writes
``11_render/final/MANIFEST.json`` (per shot: frame count, sha256 of every frame, Blender version, route, profile
settings, hash of the resolved shot it was rendered from). It REFUSES to start unless a human `final-render`
authorization is in the ledger (it never creates one), and the pinned Blender is required on the `exe` route.

Resumable at frame level: with ``resume`` the frames already on disk are kept when they are valid PNGs of the right
size AND the manifest says they were rendered with the same settings from the same resolved shot. A killed process
leaves at worst one truncated PNG, which fails the validity check and is rendered again.

`qa_final()` writes ``qa/final_frames_report.json`` (the file the FINAL_RENDER phase contract reads): frame counts
against the resolved film, size/dimension, corrupt and black frames, hashes against the manifest. Technical checks only.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .blender import require_blender
from .blenderrun import _fm_finish, _fm_framesel, _frame_cmd, scope_shots
from .errors import FMError
from .io import hash_obj, now_iso, write_json
from .ops import load_state, record_derived
from .phases import FINAL_FRAMES_REPORT
from .project import Project
from .renderprofile import cycles_settings, is_cycles, load_profile, subprocess_env
from .resolve import resolve

FINAL_DIR = "11_render/final"
MANIFEST = f"{FINAL_DIR}/MANIFEST.json"
DEFAULT_CHUNK_FRAMES = 48          # M6_SCOPE 4.3: <= 48 frames per process (long processes corrupted colours on Windows ARM)
ROUTES = ("exe", "cloud")
_IEND = b"\x00\x00\x00\x00IEND\xaeB`\x82"
_PNG_SIG = b"\x89PNG\r\n\x1a\n"


# ------------------------------------------------------------------------------------------------ helpers
def png_info(path: Path) -> tuple[int, int] | None:
    """(width, height) of a structurally complete PNG (signature, IHDR, IEND trailer), else None. No decoding."""
    try:
        size = path.stat().st_size
        if size < 57:
            return None
        with open(path, "rb") as fh:
            head = fh.read(24)
            fh.seek(size - 12)
            tail = fh.read(12)
    except OSError:
        return None
    if head[:8] != _PNG_SIG or head[12:16] != b"IHDR" or tail != _IEND:
        return None
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _name(f: int) -> str:
    return "%04d.png" % f


def _ranges(frames: list[int], chunk: int) -> list[tuple[int, int]]:
    """Sorted frame numbers -> contiguous (a, b) runs, none longer than `chunk` frames."""
    out: list[tuple[int, int]] = []
    for f in sorted(set(frames)):
        if out and f == out[-1][1] + 1 and out[-1][1] - out[-1][0] + 1 < chunk:
            out[-1] = (out[-1][0], f)
        else:
            out.append((f, f))
    return out


def _spec(a: int, b: int) -> str:
    return str(a) if a == b else f"{a}-{b}"


def _load_manifest(project: Project) -> dict:
    p = project.dir / MANIFEST
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("shots"), dict):
                return data
        except (OSError, ValueError):
            pass
    return {"schema": "fm.final_manifest/1", "shots": {}}


def _read_film(project: Project) -> dict:
    fp = project.dir / "09_resolved" / "film.json"
    if not fp.exists():
        raise FMError("09_resolved/film.json missing: run `fm resolve` first")
    return json.loads(fp.read_text(encoding="utf-8"))


def _expected_size(film: dict, width: int) -> tuple[int, int]:
    aspect = float((film.get("format") or {}).get("aspect_ratio") or 16 / 9)
    return width, int(round(width / aspect))        # the same rounding as blender/fm_blender/preview.setup_render


def _check_authorization(project: Project) -> list:
    auths = [a for a in load_state(project).authorizations if a.what == "final-render"]
    if not auths:
        raise FMError("final render refused: no human authorization recorded in the ledger. "
                      "The human runs, in a terminal: fm authorize final-render")
    return auths


def _authorized(project: Project, auths: list, ids: list[str]) -> list[str]:
    """Shots in `ids` that no recorded authorization covers (scope `film` covers everything)."""
    covered: set[str] = set()
    for a in auths:
        try:
            covered |= set(scope_shots(project, None if a.scope in ("film", "", None) else a.scope))
        except FMError:
            continue
    return [s for s in ids if s not in covered]


# ------------------------------------------------------------------------------------------------ fm blender final
def final(project: Project, repo: Path, *, scope: str | None = None, resume: bool = False, width: int | None = None,
          samples: int | None = None, route: str = "exe", chunk_frames: int | None = None, frames: str | None = None,
          jobs: int = 1, timeout_s: int = 3600, profile: str = "final") -> dict:
    if route not in ROUTES:
        raise FMError(f"--route must be one of {', '.join(ROUTES)}")
    prof = load_profile(project, repo, profile)
    if str(prof.get("output", "png")).lower() != "png":
        raise FMError(f"render profile '{profile}' has output: {prof.get('output')}, but `fm post assemble` reads PNG frames: "
                      "set output: png in config/render_profiles.yaml")
    auths = _check_authorization(project)        # refuse before touching anything else
    resolve(project, "film")
    film = _read_film(project)
    ids = scope_shots(project, scope)
    uncovered = _authorized(project, auths, ids)
    if uncovered:
        raise FMError("final render refused: the recorded authorization does not cover " + ", ".join(uncovered[:6])
                      + ". The human runs: fm authorize final-render --scope film")
    resolved = project.dir / "09_resolved"
    shots = {sid: json.loads((resolved / f"{sid}.json").read_text(encoding="utf-8")) for sid in ids}
    nomotion = [s for s in ids if not shots[s].get("motion")]
    if nomotion:
        raise FMError("no motion block (no anim file) for " + ", ".join(nomotion) + ": a final render needs every shot animated")
    sel = _fm_framesel()
    if frames and len(ids) != 1:
        raise FMError("--frames needs a scope of exactly one shot (e.g. --scope shot:SC01_SH010)")

    fmt_w = int(((film.get("format") or {}).get("resolution_px") or [1920, 1080])[0])
    width = int(width or round(fmt_w * float(prof.get("resolution_scale", 1.0))))
    samples = int(samples or prof.get("samples") or 64)
    chunk = int(chunk_frames or prof.get("chunk_frames") or DEFAULT_CHUNK_FRAMES)
    if chunk < 1 or width < 16 or samples < 1:
        raise FMError("--chunk-frames, --width and --samples must be positive")
    exp_w, exp_h = _expected_size(film, width)
    fin = _fm_finish()
    try:   # the locked finish step the builder applies at render time (look.style.glow); refuse before any work if canon asks for more
        glare = fin.glare_params(film.get("canon") or {}, width)
    except fin.FinishError as exc:
        raise FMError(f"final render refused: {exc}") from exc

    draft = route == "cloud"
    if draft:       # bpy module: never the pinned series; recorded as such and rejected by `fm qa final`
        version = _frame_cmd(repo, draft=True, resolved=resolved, out=resolved, sid=ids[0], width=width, spec="0", stamp=False,
                             samples=samples, fast=False, resume=False)[1]
    else:           # the pin is checked before any work
        version = f"blender {require_blender(repo).version}"
    settings = {"route": route, "width": exp_w, "height": exp_h, "samples": samples, "pinned": not draft,
                "profile": {**{k: prof.get(k) for k in ("engine", "resolution_scale", "samples", "motion_blur", "output")},
                            "glare": glare}}   # canon-derived: a canon change re-renders the shot, never mixes settings
    if is_cycles(prof):   # opt-in cinematic profile: every Cycles setting joins the fingerprint (EEVEE profiles keep the old one)
        settings["profile"]["cycles"] = cycles_settings(prof, samples)
    env = subprocess_env(prof, repo, samples)
    out = project.dir / FINAL_DIR
    out.mkdir(parents=True, exist_ok=True)
    logs = project.dir / "10_blender" / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    manifest = _load_manifest(project)
    jobs_list: list[tuple[str, int, int]] = []
    kept: dict[str, int] = {}
    for sid in ids:
        n = int(shots[sid]["frames"]["count"])
        wanted = sel.parse_frames(frames, n) if frames else list(range(n))
        d = out / sid
        d.mkdir(parents=True, exist_ok=True)
        rhash = project.load().current_hash(f"resolved:{sid}")
        prior = manifest["shots"].get(sid)
        same = bool(prior and prior.get("resolved_hash") == rhash and all(
            prior.get(k) == settings[k] for k in ("route", "width", "height", "samples", "pinned")) and
            prior.get("blender") == version and prior.get("profile") == settings["profile"])
        existing = sorted(d.glob("[0-9][0-9][0-9][0-9].png"))
        if not same:
            if existing and len(wanted) != n:
                raise FMError(f"{sid}: its frames were rendered with other settings or from an older resolved shot; re-render the "
                              "whole shot (omit --frames) so one shot never mixes settings")
            for f in existing:
                f.unlink()
            reuse: set[int] = set()
        else:
            reuse = set()
            if resume:
                for f in wanted:
                    p = d / _name(f)
                    if p.exists():
                        if png_info(p) == (exp_w, exp_h):
                            reuse.add(f)
                        else:
                            p.unlink()
            for f in wanted:
                if f not in reuse and (d / _name(f)).exists():
                    (d / _name(f)).unlink()
        kept[sid] = len(reuse)
        # progress stub: what a resume after a crash needs to trust the frames already on disk
        manifest["shots"][sid] = {**(prior if same else {}), "shot": sid, "scene": sid.split("_")[0], "expected_frames": n,
                                  "complete": False, "resolved_hash": rhash, "blender": version, **settings}
        for a, b in _ranges([f for f in wanted if f not in reuse], chunk):
            jobs_list.append((sid, a, b))
    manifest.update({"schema": "fm.final_manifest/1", "project": project.slug, "updated": now_iso(), "authorization": [
        {"what": a.what, "scope": a.scope, "by": a.by, "at": a.at} for a in auths][-1]})
    write_json(project.dir / MANIFEST, manifest)

    def one(job):
        sid, a, b = job
        cmd, ver = _frame_cmd(repo, draft=draft, resolved=resolved, out=out, sid=sid, width=width, spec=_spec(a, b), stamp=False,
                              samples=samples, fast=False, resume=resume, final=True)
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, **({"env": env} if env is not None else {}))
            text, ok = r.stdout + "\n" + r.stderr, "FM_OK" in r.stdout
        except (subprocess.TimeoutExpired, OSError) as exc:
            text, ok = f"{type(exc).__name__}: {exc}", False
        (logs / f"final_{sid}_{_spec(a, b)}.log").write_text(text, encoding="utf-8")
        return job, ok, ver

    with ThreadPoolExecutor(max(1, jobs)) as ex:
        results = list(ex.map(one, jobs_list))
    failed_chunks = [f"{s}:{_spec(a, b)}" for (s, a, b), ok, _ in results if not ok]

    complete, incomplete = [], {}
    for sid in ids:
        n = int(shots[sid]["frames"]["count"])
        d = out / sid
        hashes: dict[str, str] = {}
        for f in range(n):
            p = d / _name(f)
            if png_info(p) == (exp_w, exp_h):
                hashes[_name(f)] = _sha(p)
        missing = [f for f in range(n) if _name(f) not in hashes]
        ent = manifest["shots"][sid]
        ent.update({"frames": len(hashes), "frame_sha256": hashes, "blender": version, "complete": not missing,
                    "rendered_at": now_iso()})
        if missing:
            incomplete[sid] = len(missing)
        else:
            complete.append(sid)
    manifest["blender"] = version
    manifest["route"] = route
    manifest["updated"] = now_iso()
    mp = project.dir / MANIFEST
    write_json(mp, manifest)

    loaded_ids = set(_all_shot_ids(project))
    for sid in complete:
        digest = hash_obj(manifest["shots"][sid]["frame_sha256"])
        record_derived(project, f"render:final_{sid}", [f"resolved:{sid}"], content=digest, producer="fm.blender.final",
                       note=f"{version}; {route}; {exp_w}x{exp_h}; {samples} samples; {manifest['shots'][sid]['frames']} frames; png")
    done = sorted(s for s, e in manifest["shots"].items() if e.get("complete") and s in loaded_ids)
    if done:
        record_derived(project, "render:final", [f"resolved:{s}" for s in done], file=mp, producer="fm.blender.final",
                       note=f"{version}; {route}; {len(done)} complete shot(s) in the manifest")
    return {"rendered_chunks": len(results) - len(failed_chunks), "failed_chunks": failed_chunks, "complete": complete,
            "incomplete": incomplete, "frames_kept": kept, "backend": version, "route": route, "width": exp_w, "height": exp_h,
            "samples": samples, "chunk_frames": chunk, "manifest": str(mp), "pinned": not draft}


def _all_shot_ids(project: Project) -> list[str]:
    return [f.stem for f in sorted((project.dir / "09_resolved").glob("SC*.json"))]


# ------------------------------------------------------------------------------------------------ fm qa final
BLACK_MEAN, BLACK_MAX = 0.01, 0.05      # luminance (0..1) of a black frame
BLACK_RUN_OK = 12                       # a black run this long, or touching the shot's head/tail, is WARN (intentional?)


def _decode_stats(path: Path):
    """Full decode (catches truncated/corrupt data that the header check cannot) -> (mean, max) luminance, or None."""
    from PIL import Image
    try:
        with Image.open(path) as im:
            im.load()
            im = im.convert("RGB")
            im.thumbnail((160, 90))
            px = list(im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata())
    except Exception:  # noqa: BLE001 - any decode failure is a corrupt frame
        return None
    lum = [(0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 for r, g, b in px]
    return sum(lum) / len(lum), max(lum)


def qa_final(project: Project, *, allow_reduced: bool = False) -> dict:
    film = _read_film(project)
    table = {k: int(v["frames"]) for k, v in film["shots"].items()}
    total = int(film.get("total_frames", sum(table.values())))
    mp = project.dir / MANIFEST
    manifest = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else None
    if manifest is not None and not isinstance(manifest.get("shots"), dict):
        manifest = None
    out = project.dir / FINAL_DIR
    loaded = project.load()
    fmt_w = int(((film.get("format") or {}).get("resolution_px") or [1920, 1080])[0])
    rows, found_total = [], 0

    film_row = {"shot": "FILM", "findings": []}
    if manifest is None:
        film_row["findings"].append(["FAIL", "11_render/final/MANIFEST.json missing or unreadable (run `fm blender final`)"])
    else:
        extra = sorted(set(manifest["shots"]) - set(table))
        if extra:
            film_row["findings"].append(["WARN", "manifest lists shot(s) not in the resolved film: " + ", ".join(extra[:6])])
    if sum(table.values()) != total:
        film_row["findings"].append(["FAIL", f"frame table sums to {sum(table.values())}, film total_frames is {total}"])
    rows.append(film_row)

    for sid in sorted(table):
        n = table[sid]
        row = {"shot": sid, "findings": [], "metrics": {"expected_frames": n}}
        rows.append(row)
        add = row["findings"].append
        d = out / sid
        names = sorted(p.name for p in d.iterdir()) if d.is_dir() else []
        want = [_name(f) for f in range(n)]
        have = [x for x in names if x in set(want)]
        row["metrics"]["frames_found"] = len(have)
        found_total += len(have)
        if not d.is_dir() or not names:
            add(["FAIL", f"no frames in {FINAL_DIR}/{sid} (expected {n})"])
            continue
        if len(have) != n:
            miss = [x for x in want if x not in set(have)]
            add(["FAIL", f"{len(have)} frames, expected {n}; missing {', '.join(miss[:6])}" + (" ..." if len(miss) > 6 else "")])
        odd = [x for x in names if x not in set(want)]
        if odd:
            # `fm post assemble` counts every *.png in the shot directory, so extras break it
            png_odd = [x for x in odd if x.lower().endswith(".png")]
            add(["FAIL" if png_odd else "WARN", "unexpected file(s) in the shot directory: " + ", ".join(odd[:6])])
        ent = (manifest or {}).get("shots", {}).get(sid) if manifest else None
        if manifest is not None and ent is None:
            add(["FAIL", "shot is not in MANIFEST.json"])
        if ent is not None:
            if ent.get("route") != "exe" or not ent.get("pinned", False):
                add(["FAIL", f"not rendered with the pinned Blender (route {ent.get('route')}); G8 needs --route exe"])
            if not ent.get("complete"):
                add(["WARN", "manifest marks this shot incomplete (interrupted run?)"])
            cur = loaded.current_hash(f"resolved:{sid}")
            if ent.get("resolved_hash") != cur:
                add(["FAIL", "frames were rendered from a different version of the resolved shot (stale); re-render the shot"])
            row["metrics"].update({"blender": ent.get("blender"), "samples": ent.get("samples"),
                                   "size": [ent.get("width"), ent.get("height")]})
            if ent.get("width") is not None and int(ent["width"]) < fmt_w:
                add(["WARN" if allow_reduced else "FAIL",
                     f"width {ent['width']} is below the film's {fmt_w} px: not a final-resolution render"])
            if ent.get("width") is not None and (ent["width"], ent["height"]) != _expected_size(film, int(ent["width"])):
                add(["FAIL", f"manifest size {ent['width']}x{ent['height']} does not match the film aspect ratio"])
        hashes = (ent or {}).get("frame_sha256") or {}
        size_bad, hash_bad, corrupt, black, unlisted = [], [], [], [], []
        for f in range(n):
            nm = _name(f)
            p = d / nm
            if nm not in have:
                continue
            info = png_info(p)
            if info is None:
                corrupt.append(f)
                continue
            if ent is not None and ent.get("width") is not None and info != (ent["width"], ent["height"]):
                size_bad.append(f"{f}:{info[0]}x{info[1]}")
            if ent is not None:
                if nm not in hashes:
                    unlisted.append(f)
                elif _sha(p) != hashes[nm]:
                    hash_bad.append(f)
            st = _decode_stats(p)
            if st is None:
                corrupt.append(f)
            elif st[0] < BLACK_MEAN and st[1] < BLACK_MAX:
                black.append(f)
        corrupt = sorted(set(corrupt))
        if corrupt:
            add(["FAIL", f"{len(corrupt)} corrupt or truncated frame(s): " + ", ".join(map(str, corrupt[:8]))])
        if size_bad:
            add(["FAIL", f"{len(size_bad)} frame(s) differ in size from the manifest: " + ", ".join(size_bad[:6])])
        if hash_bad:
            add(["FAIL", f"{len(hash_bad)} frame(s) do not match their MANIFEST hash: " + ", ".join(map(str, hash_bad[:8]))])
        if unlisted:
            add(["FAIL", f"{len(unlisted)} frame(s) are not in the MANIFEST: " + ", ".join(map(str, unlisted[:8]))])
        if hashes and set(hashes) - set(want):
            add(["WARN", "manifest hashes frames outside the shot's range"])
        row["metrics"]["black_frames"] = black
        for a, b in _ranges(black, 10 ** 9):
            ln = b - a + 1
            if a == 0 or b == n - 1 or ln >= BLACK_RUN_OK:
                add(["WARN", f"black frames {a}-{b} ({ln}): intentional blackout/fade? check against the shot's intent"])
            else:
                add(["FAIL", f"black frame(s) {a}-{b} inside the shot: likely a render glitch"])
    if sum(table.values()) != found_total:
        film_row["findings"].append(["FAIL" if manifest is not None or found_total == 0 else "WARN",
                                     f"{found_total} frames on disk, the resolved film has {sum(table.values())}"])
    summary = {"shots": len(table), "frames_expected": sum(table.values()), "frames_found": found_total,
               "fail": sum(any(x[0] == "FAIL" for x in r["findings"]) for r in rows),
               "warn": sum(any(x[0] == "WARN" for x in r["findings"]) for r in rows)}
    report = {"schema": "fm.final_frames_report/1", "summary": summary, "rows": rows,
              "manifest_sha256": _sha(mp) if mp.exists() else None}
    rp = project.dir / FINAL_FRAMES_REPORT
    rp.parent.mkdir(parents=True, exist_ok=True)
    write_json(rp, report)
    refs = [f"resolved:{s}" for s in sorted(table) if loaded.current_hash(f"resolved:{s}")]
    record_derived(project, "qa:final", refs, file=rp, producer="fm.qa.final")
    report["report_file"] = FINAL_FRAMES_REPORT
    return report


__all__ = ["final", "qa_final", "load_profile", "png_info", "MANIFEST"]
