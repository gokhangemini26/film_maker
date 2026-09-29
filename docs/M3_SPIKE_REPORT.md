# M3 step 0 - Blender feasibility spike

Date: 2026-09-29. Machine: Windows ARM64 laptop, Blender 5.2.1 LTS (pin OK).
Scripts: `scripts/spike_m3/spike.py`, `spike2.py` (run headless with `blender -b --factory-startup --python ... -- <outdir> <engine>`). Renders stay in git-ignored `.fm_local/spike/`.

| Question | Result |
|---|---|
| Does EEVEE run headless (`-b`) on this machine? | **Yes.** `BLENDER_EEVEE` rendered 1920x1080 in the background with no display. |
| Render time for one 1080p frame (16 samples, simple scene) | EEVEE 5.9-6.9 s; Cycles CPU (16 samples) 11.4 s; Workbench also ran. A 38-shot preview pass is therefore minutes, not hours, for simple shots. Real sets will be slower and must be measured. |
| Do canon hex values render as themselves under the Standard view transform? | **Yes, exactly.** Jacket `#7C9CC4` rendered as pixel (124,156,196); sky `#F2C9A0` as (242,201,160). |
| Cel shading via Shader to RGB + constant colour ramp | **Works.** Both tones are reachable (lit tone in run 1, shadow tone in run 2, depending on light angle). A single frame showing both tones side by side on one object was not captured; it needs a rounder light test on a real character. |
| Coloured outline (inverted hull, outward Solidify with flipped normals, backface culling) | **Works.** A clean coloured outline, never black, as look canon L-rules require (run 2). |
| Cast shadow | Works, soft-edged; the hard-edged toon shadow the look wants needs a light/shadow setting pass in the builders. |

## Not tested (must be covered in M3 proper)
- Line Art or compositor outlines, grain, glow (compositor Glare), per-scene world lighting leaking into interiors.
- Phone UI as generated textures at insert sizes; the 24-frame fade.
- Proxy character rigs, and real set complexity and render time.
- Blender warns that `Material.use_nodes` is deprecated and removed in 6.0. Harmless on 5.2 LTS but the builders should avoid depending on it where an alternative exists.

## Conclusion
No blocker. The locked look (EEVEE toon, coloured outlines, exact hex) is achievable on this laptop, so **no style change request is needed** and the M3 plan stands. One practical note for the runner: Blender resolved a relative output path against `C:\`, so the runner must always pass absolute paths.
