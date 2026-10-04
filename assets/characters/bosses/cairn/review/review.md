# Cairn — author observations

Evidence digest: `5347a40fc6c370d21b3394f0b4a4e7404bf5350672855ced1fc865afeedd8941`

Selected the Cairn five-view sheet from CubeSiege. Two gray alternatives were rendered with the same camera/light/scale and receipt; A retains the slightly larger outer shoulder rim.

**silhouette**
Front and iso show a narrow stepped crest above broad square shoulders, two large separate fists, a short chest and wide boots. A retains the outer upper shoulder cells; B differs only slightly at this scale. Compared with the selected sheet, the model has more open joint gaps and simpler, squarer fists; source width/height is 0.75. The guardian massing and feature placement are retained, not a pixel-identical reconstruction.

**face_seals**
Front has an ivory brow and lower jaw around a full dark slit with two amber square eyes; side/iso confirm that brow and jaw project one grid cell. Gray cheeks form the side margins. Three warm chest seals are separately visible: two small raised centres and a larger central centre with a surrounding frame. Front gray lower borders separate the side seals from the middle plate.

**cubic_geometry**
Iso, side and top show flat square faces and discrete stair steps at the crest, shoulders, fist bottoms and boots. Pigment areas stay on existing cells. Source occupancy, actual skin matrices and emitted GLB faces were checked independently: 2042 unique rigid cubes, zero sampled intersections. The GLB preserves closed cubic fracture regions; unseen interfaces become visible at death.

**materials**
Stone gray and gray-green dominate front/back/iso. Moss patches have stepped irregular edges on shoulders, hands, back and boots. Ivory frames the eyes, brass/amber isolates the three seals, brown isolates the waist/tassel. Surfaces stay matte and flat; the reference has more small stone tone changes and softened corners, which are simplified by the strict cube requirement.

**locomotion**
Idle filmstrip shows nearly stationary heavy stance with small head/body movement. Move frames2/4 and9/11 alternate supporting and lifted boots while arms counter-swing; frame15 returns to frame0. Actual Godot reference-speed and turn/slope views show flat boot orientation and distinct stance/swing poses. The live root yaw/sway and raycast support were evaluated, with 57 corrections up to0.04377m. The demo is an in-place velocity exercise, so it does not prove horizontal foot locking in a moving battle actor.

**abilities**
Burst frames0/4 start with fists down; frames9/13 raise both fists, frame17 braces them forward, frame21 releases, and30 recovers. The Godot1.500s view shows this brace at ACTIVE entry with the radial marker. Lob starts with the right throwing arm raised and lowers by frame4; the Godot1.700s view shows landing after flight. A plain cubic stone launches above the evaluated palm at WARNING entry; game damage clocks are separate. Raw action previews are normalized1s; the real-engine recording remaps to3.7/3.6s catalog timings.

**death**
Death filmstrip shows the guardian retaining shape initially, then losing the chest/limb structure by frame25; separated cubic stones spread and lower through38/51/64. Frames76/89 retain the final heap. All633 fragments have positive-area vertical support chains to the floor and zero final speed. All730 continuous source and emitted GLB intervals were checked. Stones remain axis aligned; the last short downward packing stage is deterministic settlement rather than free rotational rubble physics.

Known limits:

- The strict cube grid replaces reference bevels and irregular cut faces with steps. Joint clearances are more open, and fists/mineral patches are simplified. No exact image match or external art approval is claimed.
- The selected reference remains candidate; final artistic acceptance belongs to the user or independent reviewer.
- Standalone Godot presentation was checked on a small slope and stated speed/yaw ranges. Adjacent CubeSiege gameplay was not changed or battle-tested.
- Current game fades death at75% of the clip. Integration must allow the complete2.954s collapse and an intended rubble hold; collider and Body hurt-flash path need integration checks.
- One mesh uses649 skin bones, including633 fracture bones. Runtime performance in the full game was not profiled.
