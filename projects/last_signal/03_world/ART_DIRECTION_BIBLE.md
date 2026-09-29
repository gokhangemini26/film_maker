---
fm:
  id: art_direction_bible
  kind: art_direction_bible
  phase: WORLD_CHARACTERS
  status: PROPOSED
  owner_role: world-designer
  derived_from:
  - ref: artifact:world_bible
    hash: sha256:6fca966b474afc3e3252fa9b922efc28cb1f755cdfbacfa62a930b83aa083a65
  - ref: artifact:screenplay
    hash: sha256:56d22d2e73f971b8a0d3c17ed54478249bc67c8f37212bc6730918daaae17022
  - ref: artifact:creative_direction
    hash: sha256:2a9437a4219a84067e09241c02b4df8f14e921dda206ac46d9b8d93faaeb44a3
  - ref: canon:tone.wordless
    hash: sha256:4b51cfae6e27a0a98fa06c7d64961ef46dfde5ae60ac2bc6680280a3d56f4975
  - ref: canon:tone.the_turn
    hash: sha256:653b9a834c3b4f01813d471792c37227f6b7476e3a4d314cc4792b6e51f5b361
  - ref: canon:tone.anti_goals
    hash: sha256:d6476842356e596dd37c3b164729c301f406236331567508fa016e50b5d7722b
  - ref: canon:world.rules.no_readable_text
    hash: sha256:a21cccd660b3af6cffb29094f0fab852e3e2fe1bd316dd2e7dcb094615bad1ae
  - ref: canon:world.rules.power
    hash: sha256:c55ced58e01c09a2eb6cd4897caac2571d2eaae59bbffe362b6fea76d7986c4d
  - ref: canon:world.rules.one_port
    hash: sha256:0b69045958e1916ad7910a6e9e88a3f99f6e90eac2963d760ffe7e889ae47df8
  - ref: canon:world.rules.time_and_sun
    hash: sha256:c4c98157eca0e16d776700681100256bb25eb79bb16e3807bfa0f4aa6ae47899
  - ref: canon:world.locations.street
    hash: sha256:e09ba271cd970fdd3c33f388e6992e0c63d5c98b2ff8e42b94428d4d4628b3db
  - ref: canon:world.locations.ren_car
    hash: sha256:e2ea8c58a8e1521ad7bcbe895601ed58797871db836afc4de4e6ebfb6b0d4e26
  - ref: canon:world.locations.corner_shop
    hash: sha256:921371c19d6f67f5749477530d1e5851498ad8785fd1c76166ce3c80f2b6cba6
  - ref: canon:world.locations.hana_room
    hash: sha256:17e13065e635469a52bccc8be174a1bbec98443a8a5f2bc0ae52e6311a2d8e2e
  - ref: canon:world.sets.street
    hash: sha256:f512f2320f0fdb1de518a7e82ed173a6a4f51a31f62540e2f3e4d2c4149180f1
  - ref: canon:world.sets.ren_car
    hash: sha256:238ade8c11d56ccb22e595cd9e42829e593e23808c6d83fbff3d5e00f541cb99
  - ref: canon:world.sets.corner_shop
    hash: sha256:ec237fef5176be584b10788bc38d48cf14cd937c1e42b64cb332319ef4e59f26
  - ref: canon:world.sets.hana_room
    hash: sha256:e19f0783497b907cbcdc58e82b81c8905c0c3456cc964bf467302f3e053c3114
  - ref: canon:world.props.phone_ren
    hash: sha256:307dcf5af82826c64a95436d6dc4dbe3d6491992f4e8374e97abede7d6ac07bf
  - ref: canon:world.props.phone_hana
    hash: sha256:99a3dc7748e00e5aaa6c4a2b46aaae4c8758d83ec2f119e67d050928da98a4eb
  - ref: canon:world.props.crank_charger
    hash: sha256:6831cc87e82e108ae32e6d7bc1757f27563d8d23a1f7278b97e810b439bb259d
  - ref: canon:world.props.charging_cable
    hash: sha256:bdbd610994d3f7c82db3ccc61e5d1625c3bde027716e8180880a673db21ed605
  - ref: canon:world.props.car_usb_adapter
    hash: sha256:a72ecd61a4028d019ce62c8e22e9fcf0d6251af698ffdd745d89661d5fd95844
  - ref: canon:world.props.shop_socket
    hash: sha256:f4dbaade29a56d1efd2cf089287cbab5cdef6078c1e8293ace9afcb51bb10d90
  - ref: canon:world.props.hana_headphones
    hash: sha256:af520fd0df7cd5a3797f8f646dd1d4e9e524d97e98d4fddc4bdf4415ab6401c8
  - ref: canon:world.props.sketchbook
    hash: sha256:e79b33b0f4bce7ea091363f9b7b0b86e8dfcfe48c5e3324bb91acf6d571936eb
  - ref: canon:world.props.desk_lamp
    hash: sha256:c562dba5e5bd2c9125e2d894f6f7f2d4410c78c39c018e94f27abfe195b79250
  serves:
  - intent.race_against_battery
  - intent.comic_then_tender
  - intent.open_hopeful_ending
  - intent.earned_last_signal
  - intent.anime_feel
  - intent.soft_but_cinematic
  summary: Art direction bible for Last Signal — buildable sets in metres for the street, car, shop and
    Hana's room, visual hierarchy per space, material families, the hero-prop table and the M3 build list.
  stamped_content_hash: sha256:3f6417db6caacd48626af618568a9b279f8692228f067d43df77eb7f38e520d2
title: Art Direction Bible
---
# Art Direction Bible — Last Signal

PROPOSED for G3. Built from the World Bible and `world.*` canon. Sizes are in
metres (Blender units). Material *character* (roughness, wear, finish) is set
here; hue, value and saturation belong to the look-director, and character
designs to the character-designer.

## Principles
1. **Shape before surface (DECISION).** Every space is read first as
   silhouettes against a sky or a glow: poles and wires, a rounded car, a lit
   doorway, a window. Detail is spent only where a hand touches something.
   *Why:* cel shading with two or three tone steps rewards clean shapes and
   punishes clutter; it is also how the MVP stays buildable
   (`intent.anime_feel`, `intent.soft_but_cinematic`).
2. **The phone is the brightest thing near him (DECISION).** Sets are arranged
   so that no practical light competes with the phone screen near Ren's face
   after the car dies: no lamp over the car, no lit display at the back of the
   shop after the blackout. *Why:* the screen's glow is the film's thread
   (CREATIVE_DIRECTION, light as motif) and the battery is the only meter
   (`intent.race_against_battery`).
3. **Pictograms, not words (USER_REQUIREMENT via `tone.wordless`,
   implemented as DECISION `world.rules.no_readable_text`).** Every surface
   that would normally carry text carries a shape or a colour block instead.
4. **Density follows the tone (DECISION).** The comic spaces (car interior,
   shop) are denser and more geometric, so the gags play against busy order. The
   tender spaces (the kerb at dusk, Hana's desk) are sparse and open, so the eye
   rests on one person and one light (`intent.comic_then_tender`).
5. **Kind wear, never grit (DECISION).** Things are used and cared for: faded,
   scuffed, softened edges. No rust holes, litter, graffiti or broken glass
   (`tone.anti_goals`: no melodrama, no cynicism).
6. **Nothing identifiable (FACT, project rule).** No logos, brands, trademarks
   or copies of a real street, shop or car model.

## Sets

### Street — `world.sets.street` (SC01 through glass, SC02, SC04, SC06)
**Coordinate frame (shared by every department):** +Y = west (down the street,
toward the sun and the shop), +X = north (across the road), Z up. Origin on the
south kerb edge, level with the centre of the car's passenger door. Road surface
z = 0; pavement z = 0.12.

| Element | Position / size (m) |
|---|---|
| South pavement | x −1.8 … 0.0 |
| Carriageway | x 0.0 … 5.5 |
| North pavement | x 5.5 … 7.3 |
| Building lines | south x −1.8; north x 7.3 (garden walls 1.0 high on these lines, houses set 2–3 m behind) |
| Ren's car body | x 0.2 … 1.68; y −1.85 … 1.55; faces +Y |
| Shop frontage | south side, y 10.5 … 15.0; door centre (−1.8, 12.0) |
| Lamp poles | (−1.5, 15.5) by the shop; (−1.5, −18.0) east |
| Other utility poles | (−1.5, 45.0) and beyond as silhouettes |
| Detail zone | y −20 … +30 |
| West railing | y = 30; beyond it open sky and distant rooftop silhouette cards |
| Sun | along +Y, about 6° up in SC01–SC03; below the horizon in SC04–SC06 |

- **Layers (looking west, the main axis):**
  - *Foreground:* kerb, the car's flank and open passenger door, Ren.
  - *Midground:* pavement running to the shop's awning and dark fascia; the lamp
    pole beside it.
  - *Background:* the railing, the open western sky with thin clouds, the wires
    crossing it, the low distant roofline.
- **Looking east (reverse):** houses, lit windows, the east lamp; a flatter,
  darker frame for the comic "world beats him" wides.
- **Entrances and eyelines:** he runs out of the car's driver door (road side)
  up the pavement to the shop door at y 12 (SC02). At the kerb (SC04) his
  eyeline to the glovebox runs through the open passenger door. In SC06 his
  eyeline goes up, to the western sky.
- **Visual hierarchy.** SC02: the running figure against the long, raking light
  down the street; the shop's awning is the target at the end of the line.
  SC04/SC06: *first* the lit phone and his face, *second* the open door and the
  glovebox, *third* the sky. The lamps are 15–18 m away so his kerb sits in the
  unlit gap; the lit windows opposite are small and dim, below the phone.
- **Materials:** asphalt (matte, fine grain, pale with age); concrete kerb
  (matte, rounded worn arris); plaster and panelled house walls (matte, soft
  weathering streaks under sills); garden walls in block (matte); poles in
  painted steel (low sheen, chipped at the base); wires (thin, dark, no
  material detail); railing (painted steel tube).
- **Dressing density: sparse.** A few potted plants by doorways, a bicycle
  leaning on one garden wall across the street (a silhouette, no brand), closed
  gates, curtains. Nothing on the south pavement between car and shop, so the
  sprint is clear.
- **Kerb sitting spot (RECOMMENDATION for cinematographer / animation-director):**
  the kerb beside the car's rear quarter (y ≈ −1.0), back against the rear side
  panel, so the open passenger door stays forward of him in frame and he can
  lean back against the car for the final image without the door in the way.

### Ren's car — `world.sets.ren_car` (SC01, SC02, SC04, SC06)
- **Footprint:** 3.40 × 1.48 m, height 1.45, wheelbase 2.30. Doors 1.05 long,
  open to 60°. Sill 0.32; seat cushion 0.45. Windscreen raked about 30°.
- **Layers (SC01, interior, looking forward):**
  - *Foreground:* steering wheel, his hands, the phone.
  - *Midground:* the dashboard with its unlabelled dials, the console socket and
    adapter, the glovebox to the left.
  - *Background:* the windscreen full of low sun and the street receding west.
  The rear-view mirror hangs top centre; tilting it toward him is the crush cue.
- **Glovebox:** opening 0.32 × 0.15, depth 0.20, lid hinged at the bottom,
  drops about 80°. 0.75 m from the driver's hand. Contents: crank charger, cable,
  a few paper napkins.
- **Visual hierarchy (SC01):** the phone first; the sun-filled windscreen is the
  big bright shape behind, so the phone reads against his darker, backlit
  silhouette. At the plant, the glovebox lid dropping and the charger landing
  are the one sudden movement in a still cabin.
- **Materials:** painted steel body (paint gone from gloss to a soft satin,
  sun-faded on the roof and bonnet); glass (glossy, the one strong specular in
  the exterior); rubber seals and tyres (matte, dark); fabric seats (matte,
  driver's side slightly shiny with wear); dashboard hard plastic (matte, fine
  grain); round headlamps (glossy covers).
- **Dressing density: medium, orderly.** The key on a plain ring; a small
  hanging charm from the mirror is **not** included (it would be a readable
  personality object for the character-designer to request if wanted).
- **Blank number plates.** Not featured in framing.

### Corner shop — `world.sets.corner_shop` (SC02, SC03; background SC04, SC06)
Shop-local frame: origin at the door threshold centre; "depth" runs into the shop;
"right" is as seen entering.

| Element | Position / size (m) |
|---|---|
| Footprint | 4.5 wide × 9.0 deep, ceiling 2.7 |
| Counter | front left, 1.8 × 0.6 × 1.0 high; plain till box (no screen) |
| Back-room doorway | behind the counter, 0.8 × 2.0, hanging strip curtain |
| Aisles | 2 gondolas, 1.5 high × 5.0 long, aisles 0.9 wide |
| Fridges | 3 across the back wall, each 0.7 × 0.7 × 2.0, glass doors, lit inside |
| Socket | back wall, right-hand corner, 0.3 above the floor, depth 8.9 |
| Display stand | freestanding, tiered, 0.6 × 0.4 × 1.3, 0.25 in front of the socket |
| Ceiling | 4 flat light panels |
| Exterior | awning 1.0 deep at 2.3 high, striped; fascia sign 3.0 × 0.5 with a basket pictogram, lit until the blackout |

- **Layers (SC03, looking toward the back wall):**
  - *Foreground:* Ren kneeling, the display stand, the cable to the socket.
  - *Midground:* the three glowing fridges.
  - *Background:* none; the back wall.
  **Reverse (looking toward the door):** the long aisle, the counter, and the
  door glass as a small pale rectangle; after the blackout this is the only
  shape beyond his lit face.
- **Visual hierarchy.** Before the blackout, the bright uniform shop is busy
  order: rows of repeated shapes, and his crouched figure is the one irregular
  shape among them. After the blackout, *first* his phone-lit face, *second* the
  faint rectangle of the door far behind, *nothing else*. Designing the frontage
  to face away from the sun and covering the glass guarantee the dark.
- **Materials:** vinyl tile floor (slightly glossy, scuffed matte down the
  aisles); powder-coated shelving (low sheen); fridge glass (glossy, reflective);
  packets (semi-gloss, simple shapes); counter laminate (matte); strip curtain
  (thin plastic strips, slight sheen).
- **Dressing density: dense but uniform.** Merchandise as arrayed primitives in
  a few shape families (round tins, tall boxes, pillow bags, bottles), each
  family in one colour family (hues by the look-director). Pictogram posters on
  the inside of the glass (an ice lolly, a starburst, a steaming cup). No labels,
  no prices, no screens.

### Hana's room — `world.sets.hana_room` (SC05)
- **Footprint:** 3.0 × 3.6 m, ceiling 2.4. Window on the west wall, 1.2 × 1.1,
  sill at 0.9, curtains open. Desk 1.1 × 0.55 at 0.72 against the window wall,
  simple desk chair.
- **Desk layout, left to right:** desk lamp (on) · pencil cup · open sketchbook
  (centre, in front of her) · her phone face-up. Four to six sketches pinned on
  the wall either side of the window.
- **Layers (looking at her from inside the room toward the window, the likely
  main angle):**
  - *Foreground:* the desk edge, the phone.
  - *Midground:* Hana, headphones, the sketchbook, the lamp.
  - *Background:* the window with the dusk sky, rooftops, a pole and wires.
- **Visual hierarchy.** *First* her face (lit by the lamp, then by the phone),
  *second* the phone waking, *third* the window sky. The phone sits on the far
  side from the lamp so its light arrives as a new light on her face.
- **Materials:** matte wood desk; paper (matte, slightly warm); pencils; fabric
  curtains (soft, matte); plaster wall (matte); bedding and shelf in soft,
  low-detail shapes.
- **Dressing density: medium, complete, balanced.** Every object has a place.
  This is the first frame in the film that feels whole.

## Hero props

| id | object | size (m) | material | story function | scenes |
|---|---|---|---|---|---|
| `world.props.phone_ren` | Ren's smartphone in a plain soft case | 0.147 × 0.071 × 0.0085; corner r 0.009 | matte soft case with worn corners; glossy screen (emissive; UI by look-director) | the meter (battery %) and the glow on his face; types and sends the invitation | SC01–SC04, SC06 |
| `world.props.crank_charger` | hand-crank charger, fold-out arm and knob | body 0.13 × 0.065 × 0.042; arm 0.085; knob ⌀0.02 × 0.022; pip ⌀0.006 | matte plastic, rubberised side grip, scuffed corners, unworn hinge | planted as a joke (SC01), chosen at the turn, turned by hand to send; the pip glows while he cranks | SC01, SC04 |
| `world.props.charging_cable` | one plain charging cable | 1.0 long, ⌀0.004 | matte soft sheath | the one thread through all three attempts | SC01–SC04, SC06 |
| `world.props.phone_hana` | Hana's smartphone, case distinct from Ren's | 0.150 × 0.072 × 0.009 | case finish to be set by character-designer + look-director; glossy screen | lights with his photo; she reads the invitation | SC05 |
| `world.props.hana_headphones` | large over-ear wireless headphones | band 0.18 wide; cups ⌀0.085 | soft-touch plastic, cushioned cups | why she missed the call; slide down to her neck | SC05 |
| `world.props.car_usb_adapter` | USB adapter in the 12 V dash socket with ring light | ⌀0.03, protrudes 0.04 | matte plastic; thin emissive ring | the car's failure in one light | SC01 |
| `world.props.shop_socket` | double wall socket with two USB ports | 0.146 × 0.086, 0.3 above floor | glossy white-ish plastic (value by look-director) | the shop attempt's target | SC03 |
| `world.props.sketchbook` | open landscape sketchbook, drawing in progress | 0.30 × 0.21 | matte paper, pencil lines | what absorbed her; rhymes with the sky | SC05 |
| `world.props.desk_lamp` | small arm desk lamp | about 0.4 high | matte painted metal | the motivated warm practical in her room | SC05 |

The car itself (`world.locations.ren_car`, `world.sets.ren_car`) is also a hero
object: 3.40 × 1.48 × 1.45, painted steel.

**Prop rules**
- No logos, badges or markings on any prop. The crank charger has **no** torch,
  radio or solar panel.
- The same port shape on the car adapter, shop socket and crank charger
  (`world.rules.one_port`).
- Hana's phone is not on a charger.
- **Coordination:** headphone fit and colour, phone case personality (if any)
  and any small personal items (a mirror charm, a keyring) are for the
  character-designer to request; all colours are for the look-director.

## Build list for M3

| Item | Approach | Detail level | Asset needed? | Licence |
|---|---|---|---|---|
| Street ground, pavements, kerbs | modelled primitives | low | no | n/a (built in-house) |
| Houses, garden walls | extruded boxes, window insets, emissive window cards for dusk | low, silhouette | no | n/a |
| Utility poles, lamps, wires, railing | cylinders, simple lamp heads, bezier curves | low | no | n/a |
| Distant roofline beyond the railing | flat silhouette cards | minimal | no | n/a |
| Sky with thin clouds | gradient / painted sky and cloud cards (look-director) | n/a | possibly a sky texture | UNKNOWN until verified if external |
| Ren's car, exterior + front half interior | modelled from primitives with subdivision; hinged door and glovebox lid | **high (hero)** | no (a base mesh could speed it up) | UNKNOWN until verified if a base mesh is used |
| Shop shell, counter, strip curtain | primitives | low | no | n/a |
| Shop aisles and merchandise | arrayed / geometry-nodes instanced primitives in shape families | low per item, dense | no | n/a |
| Fridges | boxes with emissive interior panels and glass | medium | no | n/a |
| Display stand, socket | primitives | medium (socket is an insert) | no | n/a |
| Pictogram sign and posters | flat textures drawn in-house | n/a | no | n/a (look-director supplies designs) |
| Hana's room: window wall, desk, chair, lamp | primitives | medium | no | n/a |
| Rest of Hana's room | soft blocks in shadow | minimal | no | n/a |
| Phone (x2) | rounded box + emissive screen plane | high (inserts) | UI textures from look-director | UI font / icon set licence UNKNOWN (look-director) |
| Crank charger | rounded box + hinged, spinning arm (2 axes) + emissive pip | high (inserts) | no | n/a |
| Charging cable | bezier curve, hand-posed per shot | medium | no | n/a |
| Headphones | rigid prop, two poses | medium | no | n/a |
| Sketchbook, pencils, pinned sketches | planes + textures drawn in-house | low | no | n/a |

**Flags for the cinematographer and animation-director**
- **Cable (risk):** no cable simulation in the MVP. Pose the cable as a curve per
  shot and keep most of its length out of frame in wides.
- **Sunlit windscreen (SC01):** the car interior is shot against a very bright
  windscreen. The layout supports a backlit silhouette; fill is a lighting
  decision for the look-director.
- **Shop after the blackout:** the set is designed to go nearly black. Keep a
  hint of the back wall and fridges for the eye to find if the look-director
  wants it; the set itself provides no other light.
- **Kerb geometry:** kerb 0.12 high, car 0.2 from the kerb, door open to 60°
  over a 1.8 pavement. There is room for him to sit on the pavement edge and
  lean on the car's rear quarter.
- Nothing requires more geometry than the MVP can build; no staging workaround
  is needed.
