extends SceneTree

const PreviewScene: PackedScene = preload("res://runtime/cairn_preview.tscn")
const STEP: float = 1.0 / 30.0
var _output: String = ""
var _preview: CairnPreview
var _samples: Array[Dictionary] = []
var _phase_samples: Array[Dictionary] = []
var _render: bool = true
var _frames_path: String = ""
var _movie_frame: int = 0

func _initialize() -> void:
	for argument: String in OS.get_cmdline_user_args():
		if argument.begins_with("--output="):
			_output = argument.trim_prefix("--output=")
		elif argument == "--no-render":
			_render = false
		elif argument.begins_with("--frames="):
			_frames_path = argument.trim_prefix("--frames=")
	call_deferred("_run")

func _run() -> void:
	if _output.is_empty():
		push_error("CAIRN_PROBE_FAIL: --output is required")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(_output)
	if not _frames_path.is_empty():
		DirAccess.make_dir_recursive_absolute(_frames_path)
	_preview = PreviewScene.instantiate() as CairnPreview
	_preview.probe_mode = true
	root.add_child(_preview)
	await process_frame
	await physics_frame
	if not _preview.skeleton:
		quit(1)
		return
	# Sequence contains acceleration, yaw, terrain and authored skill/death phases.
	# Every locomotion frame runs the real SkeletonModifier, including terrain rays.
	for index: int in range(36):
		await _evaluate_locomotion("idle", float(index) * STEP, Vector3.ZERO, 0.0, 0.0, false)
	await _record("idle", true)
	for index: int in range(36):
		await _evaluate_locomotion("move", float(index) * STEP * 0.5, Vector3(0.0, 0.0, -1.15), 0.0, 0.0, false)
	await _record("walk_half_speed", true)
	for index: int in range(36):
		await _evaluate_locomotion("move", float(index) * STEP, Vector3(0.0, 0.0, -2.3), 0.0, 0.0, false)
	await _record("walk_reference_speed", true)
	for index: int in range(30):
		await _evaluate_locomotion("move", float(index) * STEP * 1.35, Vector3(0.0, 0.0, -3.105), 2.4, 0.50, true)
		if index in [8, 15, 22, 29]:
			await _record("walk_fast_turn_slope_%d" % index, index == 22)
	for index: int in range(30):
		await _evaluate_locomotion("move", float(index) * STEP * 0.8, Vector3(0.0, 0.0, -1.84), -2.4, -0.50, true)
		if index in [8, 15, 22, 29]:
			await _record("walk_reverse_turn_slope_%d" % index, index == 22)
	for attack: int in range(2):
		var duration: float = 3.7 if attack == 0 else 3.6
		var boundary: float = 1.5 if attack == 0 else 1.7
		for index: int in range(ceili(duration / STEP) + 1):
			var elapsed: float = minf(float(index) * STEP, duration)
			_preview.seek_ability(attack, elapsed)
			await _settle()
			if index % 6 == 0 or absf(elapsed - boundary) < STEP * 0.6:
				await _record("attack_%d_%.3f" % [attack, elapsed], absf(elapsed - boundary) < STEP * 0.6)
	var death_length: float = _preview.animation_player.get_animation(_preview.clips["death"]).length
	for index: int in range(ceili(death_length / STEP) + 1):
		var elapsed: float = minf(float(index) * STEP, death_length)
		_preview.seek_death(elapsed)
		await _settle()
		if index % 6 == 0 or index == ceili(death_length / STEP):
			await _record("death_%.3f" % elapsed, index == ceili(death_length / STEP))
	var lengths: Dictionary = {}
	for clip: String in _preview.REQUIRED_CLIPS:
		lengths[clip] = _preview.animation_player.get_animation(_preview.clips[clip]).length
	var report: Dictionary = {
		"engine": Engine.get_version_info()["string"],
		"scope": "Self-contained asset presentation probe; no Cube Siege gameplay integration",
		"rendered": _render,
		"skeleton_bones": _preview.skeleton.get_bone_count(),
		"clips_seconds": lengths,
		"frames_evaluated": _preview.frames_evaluated,
		"modifier_evaluations": _preview.motion.modification_count,
		"foot_support_adjustments": _preview.motion.support_adjustment_count,
		"foot_sole_offset": _preview.motion.foot_sole_offset,
		"samples": _samples,
		"phase_samples": _phase_samples,
		"matrix_convention": "bone_matrices: row-major 4x4, Blender Z-up rest-world to posed-world (C^-1 * M_godot * C); bone_matrices_godot: original Godot Y-up matrix; C maps [x,y,z] to [x,z,-y]; recorded in modifier.modification_processed",
		"matrix_json_precision": "entries rounded to seven decimal places (max entry error 5e-8); engine poses are not rounded or changed",
		"limitations": ["in-place velocity exercise", "single gentle slope, no full game voxel terrain", "ability timing matches current catalog; marker mesh is a demo only", "full death preview does not use game's premature fade"],
	}
	var file: FileAccess = FileAccess.open(_output.path_join("runtime_pose_samples.json"), FileAccess.WRITE)
	if not file:
		push_error("CAIRN_PROBE_FAIL: cannot write samples")
		quit(1)
		return
	# Dense 30 Hz skin matrices can be large; omit whitespace and duplicate axes.
	file.store_string(JSON.stringify(report) + "\n")
	file.close()
	if _preview.motion.modification_count < 100 or _preview.motion.support_adjustment_count <= 0:
		push_error("CAIRN_PROBE_FAIL: motion modifier or ground support was not exercised")
		quit(1)
		return
	print("CAIRN_PROBE_COMPLETE frames=%d modifier=%d support=%d samples=%d" % [_preview.frames_evaluated, _preview.motion.modification_count, _preview.motion.support_adjustment_count, _samples.size()])
	quit(0)

func _evaluate_locomotion(clip: String, time: float, velocity: Vector3,
		yaw_rate: float, yaw: float, slope: bool) -> void:
	_preview.seek_locomotion(clip, time, velocity, yaw_rate, yaw, slope)
	await _settle()

func _settle() -> void:
	await process_frame
	await physics_frame
	if _render:
		await RenderingServer.frame_post_draw
		if not _frames_path.is_empty():
			var frame_image: Image = root.get_texture().get_image()
			var frame_error: Error = frame_image.save_png(_frames_path.path_join("frame_%05d.png" % _movie_frame))
			if frame_error != OK:
				push_error("CAIRN_PROBE_FAIL: movie frame save failed")
				quit(1)
			_movie_frame += 1
	# All evaluated frames, not just screenshots, feed whole-motion SAT checks.
	# Matrix arrays are newly allocated by the modifier signal and never mutated.
	_samples.append({"frame": "%04d_%s" % [_samples.size(), _preview.presentation_label],
		"animation_time": _preview.animation_time,
		"bone_matrices": _preview.latest_bone_matrices.duplicate(),
		"authored_articulation_matrices": _preview.latest_authored_articulation_matrices.duplicate(),
		"foot_world": _preview.latest_foot_world.duplicate(),
		"foot_support_adjustment": _preview.latest_foot_support,
		"procedural_rotation": [_preview.motion.last_motion_rotation.x,
			_preview.motion.last_motion_rotation.y, _preview.motion.last_motion_rotation.z]})

func _record(label: String, screenshot: bool) -> void:
	_phase_samples.append({"frame": label, "sample_index": _samples.size() - 1,
		"animation_time": _preview.animation_time,
		"bone_matrices_godot": _preview.latest_bone_matrices_godot.duplicate(),
		"screenshot": label + ".png" if screenshot and _render else ""})
	if screenshot and _render:
		var screenshot_image: Image = root.get_texture().get_image()
		var result: Error = screenshot_image.save_png(_output.path_join(label + ".png"))
		if result != OK:
			push_error("CAIRN_PROBE_FAIL: screenshot save failed " + label)
			quit(1)
