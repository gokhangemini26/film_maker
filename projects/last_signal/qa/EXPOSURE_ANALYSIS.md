---
fm:
  id: exposure_analysis
  kind: analysis
  phase: PREVIEW
  status: PROPOSED
  owner_role: look-director
  derived_from:
  - ref: canon:look.exposure.scene_keys
    hash: sha256:8e2d662d272976f9442271ae8ec97ae1a85ccd45826490ef6ce1cbbf022cabc4
  - ref: canon:look.exposure.value_structure
    hash: sha256:db1c7cc7ca191389eda39900701b3da8966d7e7bcd26e084e3e01bd6b5d0df38
  - ref: canon:look.style.render_constraints
    hash: sha256:5ff198e989a3e2bfe6217768a89180fee793f10f9c349cccdf50a71f00958c0e
  - ref: canon:look.color.scene.sc01
    hash: sha256:14a3283d35fb9f9026c9b3676b0c4923090af972e22dd15465b2e2470ebcdc77
  - ref: canon:look.color.scene.sc02
    hash: sha256:1a3754d6b5efa06ef64a91876f90a3e2d8382d543077cea9c6abdf465b1dabc3
  - ref: canon:look.color.scene.sc03
    hash: sha256:9f359d0eb70e79db00a61ef1c5275f3afce278d1df44b2d87261b347af7db7aa
  - ref: canon:look.color.scene.sc04
    hash: sha256:450007ba1dae2b8cb00dc8b1dc22a56a23a75d7448a7740c1ec5b6154c5b9ab8
  - ref: canon:look.color.scene.sc05
    hash: sha256:b1a78d48918a7c2680e15164744414cfef15418b774a59273336aeca4406cea9
  - ref: canon:look.color.scene.sc06
    hash: sha256:fc82371740c32b8306e12778b8389f7c265427f4bc4679b402724bc86798affb
  - ref: canon:look.lighting.sc01
    hash: sha256:0456faefddfd67f2c2c6febcf99a936c5ed6f16e1d13efef673b603911e38a4a
  - ref: canon:look.lighting.sc04
    hash: sha256:210c71d6f0cc9dfe8409897ffd19631f2ba137090a00d4989150cabbe9f56d50
  - ref: canon:look.lighting.sc06
    hash: sha256:ba5eb42513d8c3407c6ec6d390ac59bed8a91647085321471a6a83c91b975886
  - ref: qa:stills
    hash: sha256:8df7f3161f90d4ff62a68e4aa02733a037c1d19775aa41b5bab09862dd90a77b
  - ref: artifact:g5_review
    hash: sha256:be1f210ebfbb6a9ac7c04526b2ae0ad172b7ba8540121ba9e47e6b90870dee8c
  serves:
  - intent.comic_then_tender
  - intent.soft_but_cinematic
  summary: G5 finding 19. Keys and fm qa stills use the same metric (display luma), so the gap is not
    a measurement mismatch. SC04/SC06 are genuinely too bright because the builder renders dusk sets in
    their golden-hour tones. SC01, SC03 lit and SC05 keys sit at or below their own locked shadow-tint
    luma. CHANGE-007 proposed (metric written down; phone inserts measured minus the screen; numbers unchanged).
  stamped_content_hash: sha256:a2b9b93c6d181fa65f465427f66bc873ac5291ed3b60709293bc2a62d60aa5d1
title: Exposure analysis (G5 finding 19)
---
# Exposure analysis: scene keys vs pinned previews (G5 finding 19)

PROPOSED. Look-director. Nothing here changes canon or the builder. CHANGE-007 awaits a human decision.

## 1. Are the keys and the measurement on the same basis? Yes.
- FACT: `fm qa stills` (`core/fm/qa_stills.py`) computes `mean_lum` as Rec.709 weights on 8-bit sRGB code
  values (display-referred luma). It averages over a 160x90 thumbnail. I re-measured at 320x180 and got the
  same values within 0.001.
- FACT: the keys say "display-referred". CHANGE-006 computed the film floor `#1B1C29` as luma 0.11. That only
  works with the same formula (its linear luminance is 0.012).
- FACT: the previews are 8-bit PNG, Standard view transform, exposure 0, look None
  (`look.style.render_constraints`). Glare is final-only (`finish.py`). Grain is at assembly and has zero mean.
  The post plan has no grade. So no later step will darken the frame.
- Tested and rejected: "the keys are linear". Mean linear luminance happens to match SC04 (0.47 vs 0.46) and
  SC06 (0.42 vs 0.42). But it then puts SC01 0.09, SC02 0.15 and SC03 lit 0.14 *under* their keys, and the
  blackout key 0.08 would mean luma ~0.31, which contradicts CHANGE-006. A metric that fits only half the
  film is a coincidence, not the definition.
- One real definition gap: phone-screen inserts (see section 4).

## 2. Per-scene means (FACT, from `qa/stills_report.json`, whole frame)

| Key | Shots | Key ±0.06 | Render mean [range] | In band | Dominant luma | Shadow-tint luma | Verdict |
|---|---|---|---|---|---|---|---|
| SC01 | 15 | 0.62 | 0.736 [0.681-0.791] | 0/15 | 0.855 | 0.683 | Over by 0.12, and the key sits below the shadow tint |
| SC02 | 3 | 0.70 | 0.750 [0.725-0.786] | 2/3 | 0.860 | 0.716 | Close |
| SC03 lit | 4 | 0.74 | 0.781 [0.705-0.869] | 2/4 | 0.932 | 0.785 | SH010 (wide, ceiling panels) over; key at the shadow-tint floor |
| SC03 blackout | 3 | 0.08 | 0.219 [0.128-0.325] | 1/3 | n/a | n/a | Whole-frame value; CHANGE-006 regions apply (not re-measured here) |
| SC04 | 9 | 0.46 | 0.682 [0.613-0.752] | 0/9 | 0.450 | 0.551 | Too bright: render |
| SC05 | 3 | 0.52 | 0.727 [0.710-0.744] | 0/3 | 0.822 | 0.629 | Key below its own shadow tint |
| SC06 | 1 | 0.42 | 0.662 | 0/1 | 0.450 | 0.551 | Too bright: render |

The arc is the right way round (rank order SC06 < SC04 < SC05 < SC01 < SC02 < SC03 matches the keys). But it is
compressed: the keys span 0.32 and the render spans 0.12. The "lower, steady tender key" is not on screen.

## 3. Why the render is too bright where it is
- FACT (`fm_blender/util.py` `toon`): every set and character surface is a constant-ramp Shader-to-RGB
  material whose output is emission of either the lit hex or the shadow hex. Light energy only decides which
  of the two a pixel gets. It never scales brightness. So the frame mean depends on which hexes the surfaces
  carry. Turning lights down can only flip pixels to the shadow tone.
- FACT (`sets.py`, `preview.init_scene`): sets are built once, in their golden-hour hexes, with
  shadow = 0.72 x lit (linear, about 0.87 x in display). Nothing in the builder reads
  `look.color.scene.sc04/sc06` (dominant `#6F7099`, shadow tint `#8E88B4`) for set surfaces.
- FACT (images): SC04_SH010 pavement and walls render neutral grey-cream. SC04 mean RGB is about
  (161-195, 156-192, 142-186), against the dominant `#6F7099` = (111, 112, 153). Colour distance is 68-99. In
  the phone inserts (SH060/070/080) the out-of-focus street behind the phone renders at luma ~0.66 grey, not
  lavender.
- FACT (`preview.py` l.587-602): the dusk street uses world strength 0.8 for lighting and the camera sky, plus
  the afterglow sun at 2.5. Under a constant ramp, the soft-top sky light puts every upward- and
  camera-facing set face above the 0.5 threshold, so it takes the lit (day) tone.
- So SC04/SC06 are case (2): genuinely too bright. The key 0.46 is exactly the luma of the locked SC04/SC06
  dominant (0.45), so the key is consistent with canon. The builder does not implement that dominant.
- SC01 (golden hour) is also over: sun 4.0, world 0.8, plus a camera-side area fill of 90 W lights nearly every
  face the camera sees, so almost no shadow tone shows (contrast 4:1 in `look.lighting.sc01` is not on screen).

## 4. Where the key itself cannot hold (definition problems)
- **Phone-screen inserts (SC04 SH060/070/080, SC05 SH010).** FACT: the lit screen (luma ~0.95, allowed to clip
  by `look.exposure.value_structure`) covers 29-38 % of the frame. At 38 % screen, a whole-frame 0.46 needs
  the surround at about 0.16, below the value-structure floor. The key and the floor cannot both hold. This is
  the same case CHANGE-006 solved for SC03_SH060. FACT: with the screen excluded these inserts still measure
  0.61-0.67, so the render fix in section 5 is still needed.
- **SC05, SC01, SC03 lit.** FACT: each key band sits at or below the luma of the scene's own locked shadow tint
  (SC05: band top 0.58 vs shadow tint 0.629; SC01: 0.68 vs 0.683; SC03 lit: 0.80 vs 0.785). The palette has no
  large-area tone darker than the shadow tint, so a frame of only shadow tone would still miss. The keys were
  never derived from the palette (G4 finding 6). ASSUMPTION: the G4 numbers expressed the arc's shape rather
  than palette-checked values. Changing them changes the approved arc, which is a human decision (question
  below).

## 5. RECOMMENDATION

**A. Fix the render for the dusk scenes (SC04, SC06, and the SC05 window).** This implements locked canon, so
no canon change is needed. Owner: blender-td. Not implemented here.
1. Dusk set shading: for DUSK scenes, set surfaces that the afterglow sun does not reach take the scene
   dominant `#6F7099` as their shadow tone, not 0.72 x the golden-hour hex. Faces the afterglow reaches keep a
   lit tone tinted by the rim colour `#F6C69C`. Characters keep the `look.style.character_shading` model with
   shadow tint `#8E88B4`.
2. Ambient: split the world shader with an "is camera ray" mix. Camera rays see the sky at strength 1.0, so
   the dusk hexes render as themselves (`render_constraints`; today the sky is drawn at 0.8). Lighting rays
   use a low strength. Starting value 0.3 (ASSUMPTION, tune by test) so open-sky faces stay under the
   threshold and read as the lavender ambient.
3. Keep the afterglow sun (3000 K, 2 deg, 2.5) and the phone key (15 W point) as they are. They are the
   motivated sources and the only things that should carry a lit tone at dusk.
4. Estimate (ASSUMPTION, verify by re-render): SC04_SH010 lands about 0.47-0.55. Pass condition: every SC04/SC06
   shot within the key ±0.06 on the CHANGE-007 basis, and mean RGB within 60 of `#6F7099`.

**B. SC01 contrast (render).** Cut the camera-side fill from 90 to about 30 and the world lighting strength
from 0.8 to 0.4 (camera sky stays at 1.0). Non-sun faces then take the shadow tone, and the 4:1 of
`look.lighting.sc01` appears. Expect about 0.68-0.71. That puts SC01 at the edge of its band, not inside it
(section 4).

**C. Key definition: CHANGE-007 (proposed, awaiting human).** It writes down the metric (display luma, Rec.709
on sRGB codes). It also measures SC04-SC06 phone-screen inserts on the frame minus the lit screen. The numbers
are unchanged.

**D. Tooling (orchestrator / blender-td).** Add the scene-key test to `fm qa stills`. Use the CHANGE-007 basis
and the CHANGE-006 regions. Today nothing would catch this at G8.

Order: approve or reject CHANGE-007, apply A and B, re-render the previews, re-measure. Only then decide on
the SC01/SC03 lit/SC05 values with real numbers.

## Open question for the human
1. SC05 (key 0.52) cannot be reached with its locked palette, and SC01 and SC03 lit only at the edge. Should
   (a) the keys for these three scenes be re-derived from their palettes after the A/B re-render (a later
   change request, arc order kept: SC04 and SC06 lowest, SC05 between them and the comedy), or (b) the
   palettes stay and the scenes get more key-dark area by staging (a camera/world decision)? It matters because
   option (a) changes numbers you approved at G4, and option (b) changes shots approved at G5.
