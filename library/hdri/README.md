# library/hdri: HDRI environment maps (Poly Haven, CC0)

Used only by the **opt-in cinematic pipeline** (`atmosphere.hdri` in a shot or in canon `look.atmosphere*`, rendered with a Cycles
profile; see `docs/CINEMATIC_PIPELINE.md`). Nothing in a film that does not ask for an HDRI reads this folder.

## Rules

- **FILM_MAKER never downloads and never invents an HDRI.** The sandbox the agents run in cannot reach polyhaven.com anyway. You
  (the human) download the file and write its `asset.yaml`; `fm validate` and the renderer then check the record.
- One folder per HDRI: `library/hdri/<id>/` holding **one** `.hdr` or `.exr` plus `asset.yaml`. `<id>` is lowercase letters, digits,
  `_` and `-` (for example `kloofendal_48d_partly_cloudy_puresky`). Shots refer to the id only.
- A missing `asset.yaml`, a missing/`UNKNOWN`/`TODO` licence, a missing `source_url`, a `polyhaven.com` source whose licence is not
  CC0, a file name that is not a plain `.hdr`/`.exr` name, a missing file, or a `sha256` that does not match is **refused** with the
  reason (`fm validate`: `HDRI_ASSET`; the renderer raises the same error and the shot fails, it is never rendered with a stand-in).
- The image files are git-ignored (`.gitignore`: `library/hdri/*/*.hdr|exr`, 6 to 30 MB each). `asset.yaml` is committed, and its
  `sha256` pins exactly which download was used, so a second machine can fetch the same file and `fm` verifies it.
  `fm validate` reports a record without its file as a WARN (an error only when a render needs it).

## Pick and download one (about two minutes)

1. Open <https://polyhaven.com/hdris>. Filter by category/tags (outdoor, sunset, overcast, studio, ...) and open one asset.
   Its page URL is the `source_url` (`https://polyhaven.com/a/<slug>`). Every Poly Haven HDRI is CC0 (<https://polyhaven.com/license>),
   which is what `licence: CC0-1.0` records.
2. Click **Download** and choose:
   - **Resolution**: **2K** is enough for lighting and for previews (and for a background that stays soft or out of focus);
     take **4K** when the sky or background is sharp in frame in the final. 8K/16K only for a hero sky: they cost memory, not look.
   - **Format**: **HDR** (Radiance, smaller) is fine for lighting and 2K; **EXR** (half-float, larger, cleaner highlights) for 4K
     finals where the sun disc or clouds are seen directly. Both load in Blender.
   - Save it as it comes (for example `kloofendal_48d_partly_cloudy_puresky_2k.hdr`).
3. Create the folder and move the file in:

   ```
   library/hdri/kloofendal_48d_partly_cloudy_puresky/
       kloofendal_48d_partly_cloudy_puresky_2k.hdr
       asset.yaml
   ```
4. Compute the checksum (optional but recommended) and **quote it** in the YAML (an unquoted hex digest can be read as a number):

   ```
   sha256sum library/hdri/<id>/<file>                          # Linux / macOS / Git Bash
   Get-FileHash library\hdri\<id>\<file> -Algorithm SHA256     # Windows PowerShell
   ```
5. Write `asset.yaml` (template below), then `fm validate`: it must show no `HDRI_ASSET` finding.

## asset.yaml template

```yaml
# library/hdri/<id>/asset.yaml
file: kloofendal_48d_partly_cloudy_puresky_2k.hdr    # required: plain file name in this folder, .hdr or .exr
licence: CC0-1.0                                     # required: the real licence. UNKNOWN / TODO / empty are refused
source_url: https://polyhaven.com/a/kloofendal_48d_partly_cloudy_puresky   # required: where you downloaded it
resolution: 2k                                       # recommended: 1k | 2k | 4k | 8k ...
tags: [sky, outdoor, partly-cloudy, daylight]        # recommended
sha256: "0123abcd...64 hex characters..."            # recommended; QUOTED
notes: "Downloaded 2026-10-03 by <you>; sun low in the west at rotation 0."   # optional
```

Only `file`, `licence` and `source_url` are required. A `source_url` on polyhaven.com must come with a CC0 licence. An asset from
another source is allowed if you record its real licence (and check it permits your use); FILM_MAKER does not judge the licence text,
it only refuses a record that is missing or says it is unknown.

## Using it in a film

```yaml
# a shot (08_shots/SC01_SH010.shot.yaml) or the value of a canon entry look.atmosphere / look.atmosphere.<name>
atmosphere:
  hdri: {id: kloofendal_48d_partly_cloudy_puresky, rotation_deg: 120, strength: 1.0, camera_visible: true}
  rationale: "Low, cool daylight matches the brief's overcast end of day."
```

`rotation_deg` turns the sky about the vertical axis (to put the sun where the lighting bible says); `strength` multiplies the light;
`camera_visible: false` lets the HDRI light the scene while the camera still sees the painted sky.
