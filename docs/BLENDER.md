# Blender production (M3)

Blender is the production engine, not the database. Everything Blender needs is in `09_resolved/` (JSON made by `fm resolve`);
builders never read YAML or project state.

```
shots + canon --fm resolve--> 09_resolved/{shot}.json + film.json --blender/fm_blender--> 10_blender/previews/{shot}.png
```

## Commands
- `fm resolve` - deterministic engine-ready JSON (frames, camera fov, hex+linear colours, expanded canon).
- `fm blender preview [--shots A,B] [--width 768] [--jobs N]` - pinned Blender (5.2.x, refused on mismatch), one process per shot.
- `fm blender build [--draft]` - builds/updates ONE persistent `10_blender/<project>.blend` (sets, rest-pose characters, phones, one camera + `fm:<shot>` timeline marker per shot).
  Every object carries `fm_owner`/`fm_id`/`fm_hash`; a re-run rebuilds only units whose input hash changed, deletes orphans, never touches objects without `fm_owner`,
  prints built/unchanged/removed (`--json` for the full report) and records derived node `blend:<project>`. The .blend is regenerable (gitignored); `--draft` = bpy, never pinned.
- `fm blender assets [--json] [--strict]` - ASSET_PREP contract: assets shots need (`world.*`, `ui.*`) vs what the builders produce; unknown ones flagged.
- `fm blender preview --draft` - bpy module (any version), for fast iteration; records say "draft" and are not G6 evidence.
- `scripts/m3_preview_cloud.py` / `scripts/m3_preview.ps1` - the same run outside `fm` (contact sheet included);
  `scripts/m3_animatic.py <stills> <out.mp4>` - silent animatic, each still held for the shot's frame count.

## Builders (`blender/fm_blender/`)
`sets.py` street, car, shop, Hana's room from `world.sets.*`; `characters.py` proxy figures from `characters.*.proportions`;
`preview.py` per-shot camera, lights, sky, visibility, occluder culling, still render. Toon material = Diffuse -> ShaderToRGB -> ColorRamp;
outline = inverted-hull Solidify. Frames: street (+X north, +Y west), shop offset x=100, room offset x=200.

## Known limits
Static proxy poses (animation is M6), placeholder phone UI, no cable/socket/glovebox props yet, final characters need a real provider
(MPFB/VRM). Windows ARM: a single long EEVEE process can corrupt colours, hence one process per shot.
