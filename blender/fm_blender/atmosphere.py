"""Atmosphere for the OPT-IN cinematic pipeline: Poly Haven style HDRI environment light and volumetric fog.

Spec source: the `atmosphere` block of the RESOLVED shot (`09_resolved/<SHOT>.json`; a shot-level block or the canon
`look.atmosphere*` entry that `fm resolve` merged in). Applied by `apply_for_shot`, called from `preview.render_shot`, only
when the render profile selected Cycles (render_engine.ENV). A shot without the block, or an EEVEE profile, is untouched.

HDRI assets live in `library/hdri/<id>/asset.yaml` next to the .hdr/.exr it names. FILM_MAKER NEVER downloads anything and
never invents a record: the human downloads the file from polyhaven.com (CC0) and writes asset.yaml (see
library/hdri/README.md). `load_hdri_asset` refuses, with the exact reason, when the record or its licence is missing or
UNKNOWN, when the file is missing, or when a recorded sha256 does not match.

Pure Python at import time (no bpy), so `fm validate` and the unit tests can use the asset checks without Blender.
"""
from __future__ import annotations

import math
import os
import re
from pathlib import Path

HDRI_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_\-]{0,63}$")
HDRI_EXT = (".hdr", ".exr")
BAD_LICENCE = {"", "unknown", "todo", "tbd", "?", "n/a", "na", "none", "null"}
CC0_NAMES = {"cc0", "cc0-1.0", "cc0 1.0", "cc-0", "public domain (cc0)", "creative commons zero"}
REQUIRED_KEYS = ("file", "licence", "source_url")


class AtmosphereError(ValueError):
    """An atmosphere spec or HDRI record that cannot be honoured. The message says what to fix."""


# ------------------------------------------------------------------------------------------------ library
def library_root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    env = os.environ.get("FM_LIBRARY_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / "library"       # builders ship inside the repository


def _scalar(v: str):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if v.lower() in ("null", "~", ""):
        return None
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if re.fullmatch(r"-?\d+\.\d+", v):
        return float(v)
    return v


def parse_simple_yaml(text: str) -> dict:
    """Flat `key: value` YAML with inline `[a, b]` or `- item` lists: all an asset.yaml needs. Used only when PyYAML is
    not importable (the pinned Blender's bundled Python has none)."""
    out: dict = {}
    key = None
    for raw in text.splitlines():
        line = raw.split(" #", 1)[0].rstrip() if not raw.lstrip().startswith("#") else ""
        if not line.strip():
            continue
        m = re.match(r"^\s+-\s+(.*)$", line)
        if m and key is not None:
            out.setdefault(key, [])
            if isinstance(out[key], list):
                out[key].append(_scalar(m.group(1)))
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", line)
        if not m:
            raise AtmosphereError(f"asset.yaml line not understood: {raw!r}")
        key, val = m.group(1), m.group(2).strip()
        if val.startswith("[") and val.endswith("]"):
            out[key] = [_scalar(x) for x in val[1:-1].split(",") if x.strip()]
        elif val == "":
            out[key] = []
        else:
            out[key] = _scalar(val)
    return out


def _load_yaml_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml
    except ImportError:
        return parse_simple_yaml(text)
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise AtmosphereError(f"{path} must be a YAML mapping")
    return data


def _sha256(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_hdri_asset(hdri_id: str, root: str | Path | None = None, *, require_file: bool = True) -> dict:
    """The validated record of library/hdri/<id>/: {id, dir, file, path, licence, source_url, resolution, tags, sha256}.
    Raises AtmosphereError (never downloads, never guesses) when it cannot be trusted."""
    if not isinstance(hdri_id, str) or not HDRI_ID_RE.match(hdri_id):
        raise AtmosphereError(f"invalid hdri id {hdri_id!r} (lowercase letters, digits, '_' and '-')")
    d = library_root(root) / "hdri" / hdri_id
    rel = f"library/hdri/{hdri_id}"
    ay = d / "asset.yaml"
    if not ay.is_file():
        raise AtmosphereError(
            f"HDRI '{hdri_id}': {rel}/asset.yaml not found. FILM_MAKER never downloads or invents an HDRI: download the .hdr/.exr "
            f"from https://polyhaven.com/hdris (CC0) into {rel}/ and write asset.yaml (template in library/hdri/README.md)")
    data = _load_yaml_file(ay)
    missing = [k for k in REQUIRED_KEYS if not str(data.get(k) or "").strip()]
    if missing:
        raise AtmosphereError(f"HDRI '{hdri_id}': {rel}/asset.yaml is missing {', '.join(missing)}")
    licence = str(data["licence"]).strip()
    if licence.lower() in BAD_LICENCE:
        raise AtmosphereError(f"HDRI '{hdri_id}': licence is {licence!r}; record the real licence (Poly Haven HDRIs are CC0) "
                              "before the asset can be used")
    src = str(data["source_url"]).strip()
    if "polyhaven.com" in src.lower() and licence.lower() not in CC0_NAMES:
        raise AtmosphereError(f"HDRI '{hdri_id}': source_url is polyhaven.com but licence is {licence!r}; Poly Haven assets are "
                              "CC0, so this record is wrong or the asset is not from Poly Haven. Fix asset.yaml")
    if data.get("sha256") is not None and not isinstance(data["sha256"], str):
        raise AtmosphereError(f"HDRI '{hdri_id}': sha256 in {rel}/asset.yaml must be a quoted string (an unquoted hex digest can be "
                              "read as a number)")
    fname = str(data["file"]).strip()
    if "/" in fname or "\\" in fname or fname.startswith(".") or not fname.lower().endswith(HDRI_EXT):
        raise AtmosphereError(f"HDRI '{hdri_id}': file {fname!r} must be a plain file name ending in {' or '.join(HDRI_EXT)} "
                              "inside its own folder")
    path = d / fname
    if require_file:
        if not path.is_file():
            raise AtmosphereError(f"HDRI '{hdri_id}': {rel}/{fname} not found. Download it from {src} (the sandbox cannot reach "
                                  "polyhaven.com; the human does this) and keep the file name equal to asset.yaml `file`")
        want = str(data.get("sha256") or "").strip().lower()
        if want and _sha256(path) != want:
            raise AtmosphereError(f"HDRI '{hdri_id}': {rel}/{fname} does not match the sha256 recorded in asset.yaml "
                                  "(wrong or corrupted download)")
    tags = data.get("tags") or []
    return {"id": hdri_id, "dir": str(d), "file": fname, "path": str(path), "licence": licence, "source_url": src,
            "resolution": str(data.get("resolution") or ""), "tags": list(tags) if isinstance(tags, list) else [tags],
            "sha256": str(data.get("sha256") or "") or None}


# ------------------------------------------------------------------------------------------------ pure planning
def _hex_to_linear(h: str) -> list[float]:
    s = h.lstrip("#")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", s):
        raise AtmosphereError(f"colour must be #RRGGBB, got {h!r}")
    c = [int(s[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def normalise(spec: dict) -> dict:
    """Defaults + range checks for a resolved atmosphere block. Pure; returns {'hdri': {...}|None, 'fog': {...}|None}."""
    if not isinstance(spec, dict) or not (spec.get("hdri") or spec.get("fog")):
        raise AtmosphereError("atmosphere needs at least one of hdri, fog")
    out: dict = {"hdri": None, "fog": None}
    h = spec.get("hdri")
    if h:
        out["hdri"] = {"id": h["id"], "rotation_deg": float(h.get("rotation_deg", 0.0)), "strength": float(h.get("strength", 1.0)),
                       "camera_visible": bool(h.get("camera_visible", True))}
        if out["hdri"]["strength"] < 0:
            raise AtmosphereError("hdri.strength must be >= 0")
    f = spec.get("fog")
    if f:
        fog = {"density": float(f["density"]), "anisotropy": float(f.get("anisotropy", 0.0)),
               "height_falloff": float(f.get("height_falloff", 0.0)), "colour": str(f.get("colour", "#FFFFFF")).upper(),
               "bounds": f.get("bounds", "world"), "box": f.get("box")}
        if fog["density"] <= 0:
            raise AtmosphereError("fog.density must be > 0")
        if not -0.99 <= fog["anisotropy"] <= 0.99:
            raise AtmosphereError("fog.anisotropy must be within [-0.99, 0.99]")
        if fog["height_falloff"] < 0:
            raise AtmosphereError("fog.height_falloff must be >= 0")
        if fog["bounds"] not in ("world", "box"):
            raise AtmosphereError("fog.bounds must be 'world' or 'box'")
        if fog["bounds"] == "box" and not fog["box"]:
            raise AtmosphereError("fog.bounds is 'box' but fog.box is missing")
        _hex_to_linear(fog["colour"])
        out["fog"] = fog
    return out


# ------------------------------------------------------------------------------------------------ bpy side
def _world_tree(scene):
    import bpy
    w = scene.world or bpy.data.worlds.new("fm.world")
    scene.world = w
    try:
        w.use_nodes = True
    except Exception:  # noqa: BLE001 - Blender 5.x: node worlds are always on
        pass
    nt = w.node_tree
    out = next((n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputWorld"), None) or nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.get("Background") or next((n for n in nt.nodes if n.bl_idname == "ShaderNodeBackground"), None)
    if bg is None:
        bg = nt.nodes.new("ShaderNodeBackground")
        nt.links.new(bg.outputs[0], out.inputs[0])
    return nt, bg, out


def _drop(nt, prefix):
    for n in [n for n in nt.nodes if n.name.startswith(prefix)]:
        nt.nodes.remove(n)


def apply_hdri(scene, hdri_id, rotation_deg=0.0, strength=1.0, *, camera_visible=True, root=None, log=print) -> dict:
    """Light (and, unless camera_visible is false, back) the scene with library/hdri/<hdri_id>/. The world's existing
    'Background' node keeps its name, so code that later sets the world strength (preview.render_shot) still finds it."""
    import bpy

    asset = load_hdri_asset(hdri_id, root)
    nt, bg, _out = _world_tree(scene)
    _drop(nt, "fm_hdri")
    prev = bg.inputs[0].links[0].from_socket if bg.inputs[0].links else None
    prev_colour = tuple(bg.inputs[0].default_value)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.name = "fm_hdri_coord"
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.name = "fm_hdri_mapping"
    mp.inputs["Rotation"].default_value[2] = math.radians(rotation_deg)
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.name = "fm_hdri_env"
    env.image = bpy.data.images.load(asset["path"], check_existing=True)
    try:
        env.image.colorspace_settings.name = "Linear Rec.709"
    except (TypeError, ValueError):
        pass                                   # the OCIO config names its scene-linear space differently; Blender's default stands
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    colour = env.outputs["Color"]
    if not camera_visible:
        lp = nt.nodes.new("ShaderNodeLightPath")
        lp.name = "fm_hdri_lightpath"
        mix = nt.nodes.new("ShaderNodeMix")
        mix.name = "fm_hdri_mix"
        mix.data_type = "RGBA"
        nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Factor"] if "Factor" in mix.inputs else mix.inputs[0])
        a = next(s for s in mix.inputs if s.identifier == "A_Color")
        b = next(s for s in mix.inputs if s.identifier == "B_Color")
        nt.links.new(colour, a)
        if prev is not None:
            nt.links.new(prev, b)             # the painted sky stays what the camera sees
        else:
            b.default_value = prev_colour     # ... or the world's flat colour
        colour = next(s for s in mix.outputs if s.identifier == "Result_Color")
    nt.links.new(colour, bg.inputs[0])
    bg.inputs[1].default_value = float(strength)
    rep = {"hdri": hdri_id, "file": asset["file"], "licence": asset["licence"], "source_url": asset["source_url"],
           "resolution": asset["resolution"], "rotation_deg": rotation_deg, "strength": strength, "camera_visible": camera_visible}
    log("FM_HDRI " + " ".join(f"{k}={v}" for k, v in rep.items()))
    return rep


def _fog_scatter(nt, density, anisotropy, height_falloff, colour):
    sc = nt.nodes.new("ShaderNodeVolumeScatter")
    sc.name = "fm_fog_scatter"
    sc.inputs["Color"].default_value = (*_hex_to_linear(colour), 1.0)
    sc.inputs["Anisotropy"].default_value = float(anisotropy)
    dens = sc.inputs["Density"]
    if height_falloff > 0:
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        geo.name = "fm_fog_geo"
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        sep.name = "fm_fog_z"
        neg = nt.nodes.new("ShaderNodeMath")
        neg.name = "fm_fog_neg"
        neg.operation = "MULTIPLY"
        neg.inputs[1].default_value = -float(height_falloff)
        ex = nt.nodes.new("ShaderNodeMath")
        ex.name = "fm_fog_exp"
        ex.operation = "EXPONENT"
        scale = nt.nodes.new("ShaderNodeMath")
        scale.name = "fm_fog_scale"
        scale.operation = "MULTIPLY"
        scale.inputs[1].default_value = float(density)
        nt.links.new(geo.outputs["Position"], sep.inputs[0])
        nt.links.new(sep.outputs["Z"], neg.inputs[0])
        nt.links.new(neg.outputs[0], ex.inputs[0])      # EXPONENT: e ** input
        nt.links.new(ex.outputs[0], scale.inputs[0])
        nt.links.new(scale.outputs[0], dens)
    else:
        dens.default_value = float(density)
    return sc


def apply_volumetric_fog(scene, density, anisotropy=0.0, height_falloff=0.0, colour="#FFFFFF", *, bounds="world", box=None,
                         log=print) -> dict:
    """Volumetric fog. bounds='world': a world volume (uniform, or density*exp(-height_falloff*z)). bounds='box': a bounded
    volume cube (box={'center': (x,y,z), 'size': (sx,sy,sz)}) for a local fog bank; it is a shot object (cleared with the
    shot) and carries fm_owner."""
    import bpy

    spec = normalise({"fog": {"density": density, "anisotropy": anisotropy, "height_falloff": height_falloff, "colour": colour,
                              "bounds": bounds, "box": box}})["fog"]
    try:
        scene.cycles.volume_bounces = max(int(scene.cycles.volume_bounces), 2)      # multiple scattering gives the haze its glow
    except (AttributeError, TypeError):
        pass
    if spec["bounds"] == "world":
        nt, _bg, out = _world_tree(scene)
        _drop(nt, "fm_fog")
        sc = _fog_scatter(nt, spec["density"], spec["anisotropy"], spec["height_falloff"], spec["colour"])
        nt.links.new(sc.outputs["Volume"], out.inputs["Volume"])
    else:
        from . import util as U
        for o in [o for o in bpy.data.objects if o.name == "fm_fog_box"]:
            bpy.data.objects.remove(o, do_unlink=True)
        mat = bpy.data.materials.new("fm.fog.box")
        mat.use_nodes = True
        for n in list(mat.node_tree.nodes):
            mat.node_tree.nodes.remove(n)
        sc = _fog_scatter(mat.node_tree, spec["density"], spec["anisotropy"], 0.0, spec["colour"])
        mo = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
        mat.node_tree.links.new(sc.outputs["Volume"], mo.inputs["Volume"])
        me = bpy.data.meshes.new("fm_fog_box")
        s = [0.5 * v for v in spec["box"]["size"]]
        verts = [(x * s[0], y * s[1], z * s[2]) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
        faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        me.from_pydata(verts, [], faces)
        me.materials.append(mat)
        ob = bpy.data.objects.new("fm_fog_box", me)
        ob.location = spec["box"]["center"]
        ob.display_type = "WIRE"
        ob.visible_shadow = False
        U.tag(ob, "fog_box")
        ob["fm_shot"] = True                    # preview.clear_shot_objects removes it with the shot
        (bpy.data.collections.get("fm.rig") or scene.collection).objects.link(ob)
    rep = {"fog": spec["bounds"], "density": spec["density"], "anisotropy": spec["anisotropy"],
           "height_falloff": spec["height_falloff"], "colour": spec["colour"]}
    log("FM_FOG " + " ".join(f"{k}={v}" for k, v in rep.items()))
    return rep


def apply_atmosphere(scene, spec: dict, *, root=None, log=print) -> dict:
    n = normalise(spec)
    rep: dict = {}
    if n["hdri"]:
        h = n["hdri"]
        rep["hdri"] = apply_hdri(scene, h["id"], h["rotation_deg"], h["strength"], camera_visible=h["camera_visible"], root=root, log=log)
    if n["fog"]:
        f = n["fog"]
        rep["fog"] = apply_volumetric_fog(scene, f["density"], f["anisotropy"], f["height_falloff"], f["colour"],
                                          bounds=f["bounds"], box=f["box"], log=log)
    return rep


def apply_for_shot(scene, shot: dict, log=print) -> dict | None:
    """The hook `preview.render_shot` calls for every shot. Returns None without touching anything when the shot has no
    atmosphere block or the render profile did not select Cycles (an EEVEE film ignores the block, with one log line)."""
    spec = shot.get("atmosphere")
    if not spec:
        return None
    from . import render_engine as RE
    if RE.profile_from_env() is None:
        log(f"FM_ATMOSPHERE skipped {shot.get('shot_id')}: the shot has an atmosphere block but the render profile is not a Cycles "
            "(cinematic) profile; select one with --profile")
        return None
    return apply_atmosphere(scene, spec, log=log)
