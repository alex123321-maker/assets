# Cairn asset tools

The canonical editable character is
`assets/characters/bosses/cairn/source/model.blend`, with its layered lattice in
`source/voxels.json`. The delivered GLB has one skinned mesh, three materials,
16 articulated bones and 633 rigid fracture bones. Every occupied cell is a
0.10 m cube. Internal faces inside one fracture cube are culled; interfaces
between fracture cubes remain closed because they become exposed during death.

## Authoring

Authoring changes source and must be completed before a build:

```powershell
python tools/cairn/author_cairn.py
python tools/cairn/author_death_motion.py
& $env:BLENDER_BIN --background --factory-startup --python-exit-code 1 --python tools/cairn/author_blend.py
```

Set `BLENDER_BIN` to the installed Blender 5.2 executable. The death authoring
command needs NumPy and may take about 90 seconds. Run it with a finite process
deadline. It validates every continuous linear interval, support chains to the
floor, and a stationary final hold. Its final downward packing step is a
deterministic settlement of the already scattered stones, not free rigid-body
rotation. Stones keep cubic shape and zero rotation throughout.

Do not call `FCurve.update()` after filling sorted fractional death keys:
Blender merges close events. The source and GLB retain those keys with LINEAR
interpolation; export uses ACTIONS with forced sampling disabled. The binary GLB
verifier checks the actual emitted cube surfaces, skin bindings, event times,
centres and continuous swept volumes.

Blender's exporter deduplicates sampled channels through a set containing random
object UUIDs. The build temporarily sorts these channels by stable type/property/
bone fields, then restores the exporter function. Channel data is unchanged.
Review rendering uses fixed-seed 64-sample Cycles CPU with adaptive sampling and
denoising disabled. PNG cleanup removes volatile path/date/timing annotations
without changing the compressed pixels or color metadata. These choices make
the exported binary, frame hashes and videos reproducible in a clean checkout.

## Frozen-source build

```powershell
python tools/quality_gate.py build assets/characters/bosses/cairn
python tools/quality_gate.py verify-clean assets/characters/bosses/cairn
python -m unittest discover -s tests/unit -p "test_cairn*.py"
```

The recipe reads frozen source, renders two gray blockouts and six views,
exports and verifies GLB, checks authored poses at 60 Hz, renders clips at
30 fps, composes PNG/MP4 media, and runs a real Godot 4.6 preview plus dense
post-modifier cube checks. A shared 600 second deadline bounds all stages.
Build logs live in `.local/cairn_build_logs`. `BLENDER_BIN` and `GODOT_BIN`
override the machine defaults; FFmpeg must be on PATH. Python needs Pillow
and NumPy. Build never writes source or artistic verdicts.

## Preview and integration

```powershell
python tools/cairn/run_godot_probe.py --render --movie
```

The command prints the retained isolated Godot project path. Open its
`project.godot` in Godot and run the main scene for the looping presentation.
The source runtime README documents the live motion modifier interface and
CubeSiege phase remapping. The preview demonstrates the actual GLB in Godot;
it does not modify the adjacent game checkout or validate the full boss battle.

Keep `idle` and `move` looping, and use gameplay speed to scale the 0.5 second
walk cycle (reference 2.3 m/s). `attack_0` and `attack_1` are normalized one
second clips. The throw releases at WARNING entry. Full death is 2.954 seconds;
delay the current game's 75% fade if the final stone pile should remain visible.
The geometry is 2.4 m wide, 1.0 m deep, 3.2 m high, with a bottom-centre pivot
and glTF -Z forward. Check the intended collider and hurt-flash material paths
when integrating; the visual mesh is named `Body`.

Pose checks cover the delivered clips and demonstrated speed/turn/slope range.
New procedural limits, terrain or gameplay pose combinations require renewed
clearance checks. Technical checks are separate from user/external art acceptance.
