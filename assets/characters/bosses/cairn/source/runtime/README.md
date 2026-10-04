# Cairn runtime presentation

Godot 4.6 source components for the exported `output/model.glb`. These files are
presentation assets. They do not change Cube Siege or own damage, attack radius,
cooldown, body movement, navigation or collision.

`cairn_motion_modifier.gd` is a real `SkeletonModifier3D`, attached directly to the
imported `Skeleton3D`. It layers velocity- and turn-dependent whole-body yaw and
horizontal sway over the current animation. Pelvis, spine, head and limbs receive
one shared correction, preserving their authored cube clearances. Independent
torso/head lean closed those interfaces in the engine and was replaced after dense
pose checks. Secondary motion is evaluated at runtime rather than baked into move.

For stance feet, downward physics rays sample the support surface. A conservative
analytic two-bone solve raises a foot that penetrates support, capped at 0.12 m.
It solves in the authored sagittal hinge plane and retains lateral hip/knee offsets,
including the rear-edge hinge location; it does not add arbitrary 3D shin angles.
Swing feet keep their authored arcs; ankle rotation stays authored. This supports
small unevenness and gentle slopes. It is not navigation, stair climbing, a full
foot-lock solver or a replacement for body collision.

## Owner interface

Call `set_motion(collision_resolved_world_velocity, yaw_rate_radians_per_second,
ability_weight, grounded, dying)` before skeleton evaluation. In normal locomotion,
ability weight is zero. During a committed skill it is one, disabling motion and
foot corrections while the authored action owns the silhouette. `dying=true`
disables every correction and lets all rubble bones follow the death clip.

Expose `reference_speed=2.3`, response, body yaw/turn limits, sway, foot support
toggle, ankle-to-sole offset, maximum correction, ray extent and collision mask in
the Inspector. Exclude the actor from the ground collision layer. The sample scene
derives the ankle-to-sole offset from the foot rest height. If a delivered model has
another origin or footwear shape, provide its measured sole offset explicitly.

The expected bones are `root`, `pelvis`, `spine`, `head`, `upper_arm.L/R`,
`forearm.L/R`, `hand.L/R`, `thigh.L/R`, `shin.L/R`, `foot.L/R`. Additional
`rubble_*` bones remain authored. Godot uses meters, Y up and facing -Z.

## Authored animation contract

Keep `idle` and `move` looping. The baked move cycle remains useful when the
modifier is disabled. Scale its rate using collision-resolved horizontal velocity.
The true procedural secondary motion is evaluated independently of that cycle.

Keep `attack_0` and `attack_1` exactly one second. Existing `SiegeBoss` maps its
WARNING to clip time 0..0.65, ACTIVE to 0.65..0.80, and RECOVERY to 0.80..1.0.
Burst impact is at 0.65. The lob projectile starts flying at warning start, so its
release belongs at the start of `attack_1`; 0.65 is landing, not release.

The demo uses current catalog durations: burst 1.5 / 0.30 / 1.9 s, lob
1.7 / 0.30 / 1.6 s. Rings and the flight mesh are presentation demonstrations,
not damage queries or gameplay integration. The demo plays the entire death clip
and holds rubble without scaling the actor away. Existing game code instead begins
its fade after 75% of a death clip; integration must address that cutoff.

## Probe and preview

From the asset repository root:

```powershell
python tools/cairn/run_godot_probe.py --check-only
python tools/cairn/run_godot_probe.py --render --movie
```

`--check-only` parses all scripts and does not claim model behavior. The full probe
loads the real GLB, checks bones and action durations, exercises half/reference/fast
speeds, yaw in both directions, a gentle slope, both skills and full death. It fails
if the modifier or actual raycast support did not run. Every process is bounded by
one total 300 second deadline. Timeout and parser/runtime failure stop the command.

The runner retains an isolated project under `.local/cairn_runtime/<unique-id>`;
its main scene is an interactive looping preview. No existing scratch directory or
game cache is deleted. `--godot` overrides the binary path. `--movie` requires
ffmpeg and renders deterministic phase steps into PNG frames before encoding MP4.
The probe provides screenshots and `runtime_pose_samples.json` under `review/godot`.

`bone_matrices` are row-major 4x4 maps from canonical Blender Z-up rest-world
coordinates to posed-world Blender coordinates, converted from the engine result
as `C^-1 * M_godot * C`, where C maps `[x,y,z]` to Godot `[x,z,-y]`.
Every evaluated 30 Hz frame is retained in `samples`, not just screenshot phases.
`phase_samples` contains sparse phase/screenshot labels and original Godot Y-up
maps as `bone_matrices_godot`; `foot_world` uses Godot coordinates. Matrices are
sampled during `modification_processed`,
after the real pose modifier. The JSON reports support correction counts and
limitations. It is evidence for structural/pose checks, not an art verdict or proof
of Cube Siege gameplay integration.

JSON matrix entries are rounded to seven decimal places (at most 5e-8 per entry)
for manageable dense evidence. Evaluated engine transforms remain unchanged.

API sources: [SkeletonModifier3D](https://docs.godotengine.org/en/4.6/classes/class_skeletonmodifier3d.html),
[Skeleton3D](https://docs.godotengine.org/en/4.6/classes/class_skeleton3d.html),
[GLTFDocument](https://docs.godotengine.org/en/4.6/classes/class_gltfdocument.html).
