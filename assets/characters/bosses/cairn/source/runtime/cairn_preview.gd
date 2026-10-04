extends Node3D
class_name CairnPreview

const MotionModifierScript: Script = preload("cairn_motion_modifier.gd")
const REQUIRED_CLIPS: PackedStringArray = ["idle", "move", "attack_0", "attack_1", "death"]
const REQUIRED_BONES: PackedStringArray = ["root", "pelvis", "spine", "head", "upper_arm.L", "upper_arm.R", "forearm.L", "forearm.R", "hand.L", "hand.R", "thigh.L", "thigh.R", "shin.L", "shin.R", "foot.L", "foot.R"]
const BURST_WINDUP: float = 1.5
const BURST_ACTIVE: float = 0.30
const BURST_RECOVERY: float = 1.9
const LOB_WINDUP: float = 1.7
const LOB_ACTIVE: float = 0.30
const LOB_RECOVERY: float = 1.6
const FIXED_STEP: float = 1.0 / 30.0

@export var model_file: String = "res://cairn.glb"
@export var probe_mode: bool = false
var model: Node3D
var skeleton: Skeleton3D
var animation_player: AnimationPlayer
var motion: CairnMotionModifier
var clips: Dictionary[String, StringName] = {}
var latest_bone_matrices: Dictionary = {}
var latest_bone_matrices_godot: Dictionary = {}
var latest_authored_articulation_matrices: Dictionary = {}
var latest_foot_world: Dictionary = {}
var latest_foot_support: float = 0.0
var frames_evaluated: int = 0
var animation_time: float = 0.0
var presentation_label: String = "idle"
var _clock: float = 0.0
var _status: Label
var _floor: StaticBody3D
var _actor: Node3D
var _burst_marker: MeshInstance3D
var _lob_marker: MeshInstance3D
var _projectile: MeshInstance3D
var _camera: Camera3D
var _bind_skeleton_world: Transform3D = Transform3D.IDENTITY
var _lob_launch: Vector3 = Vector3.ZERO
var _lob_launch_cached: bool = false

func _ready() -> void:
	_build_stage()
	var document: GLTFDocument = GLTFDocument.new()
	var state: GLTFState = GLTFState.new()
	var error: Error = document.append_from_file(model_file, state)
	if error != OK:
		push_error("CAIRN_LOAD_FAIL: %s (%s)" % [model_file, error])
		get_tree().quit(1)
		return
	model = document.generate_scene(state) as Node3D
	if not model:
		push_error("CAIRN_LOAD_FAIL: GLTFDocument produced no scene")
		get_tree().quit(1)
		return
	_actor.add_child(model)
	var skeleton_nodes: Array[Node] = model.find_children("*", "Skeleton3D", true, false)
	var animation_nodes: Array[Node] = model.find_children("*", "AnimationPlayer", true, false)
	if skeleton_nodes.is_empty() or animation_nodes.is_empty():
		push_error("CAIRN_RIG_FAIL: Skeleton3D or AnimationPlayer missing")
		get_tree().quit(1)
		return
	skeleton = skeleton_nodes[0] as Skeleton3D
	_bind_skeleton_world = skeleton.global_transform
	animation_player = animation_nodes[0] as AnimationPlayer
	animation_player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	skeleton.modifier_callback_mode_process = Skeleton3D.MODIFIER_CALLBACK_MODE_PROCESS_MANUAL
	for clip: String in REQUIRED_CLIPS:
		for actual: StringName in animation_player.get_animation_list():
			if actual == clip or String(actual).ends_with("/" + clip):
				clips[clip] = actual
		if not clips.has(clip):
			push_error("CAIRN_CLIP_FAIL: " + clip)
			get_tree().quit(1)
			return
	for bone_name: String in REQUIRED_BONES:
		if skeleton.find_bone(bone_name) < 0 and skeleton.find_bone(bone_name.replace(".", "_")) < 0:
			push_error("CAIRN_BONE_FAIL: " + bone_name)
			get_tree().quit(1)
			return
	for action_clip: String in ["attack_0", "attack_1"]:
		if absf(animation_player.get_animation(clips[action_clip]).length - 1.0) > 0.002:
			push_error("CAIRN_CLIP_FAIL: action clips must be one second for the runtime remap")
			get_tree().quit(1)
			return
	for loop_clip: String in ["idle", "move"]:
		animation_player.get_animation(clips[loop_clip]).loop_mode = Animation.LOOP_LINEAR
	motion = MotionModifierScript.new() as CairnMotionModifier
	motion.name = "ProceduralMotion"
	skeleton.add_child(motion)
	# Foot bone origin is the ankle; derive sole offset from its rest height.
	var foot_index: int = skeleton.find_bone("foot.L")
	if foot_index < 0:
		foot_index = skeleton.find_bone("foot_L")
	motion.foot_sole_offset = (skeleton.global_transform * skeleton.get_bone_global_rest(foot_index).origin).y
	motion.modification_processed.connect(_on_modifier_processed)
	print("CAIRN_MODEL_LOADED bones=%d animations=%s ankle_offset=%.4f" % [skeleton.get_bone_count(), animation_player.get_animation_list(), motion.foot_sole_offset])
	seek_locomotion("idle", 0.0, Vector3.ZERO, 0.0, 0.0, false)

func _process(delta: float) -> void:
	if probe_mode or not skeleton:
		return
	_clock += minf(delta, 0.1)
	var t: float = fmod(_clock, 18.3)
	if t < 2.0:
		seek_locomotion("idle", t, Vector3.ZERO, 0.0, 0.0, false)
	elif t < 5.0:
		seek_locomotion("move", (t - 2.0) * 0.5, Vector3(0.0, 0.0, -1.15), 0.0, 0.0, false)
	elif t < 8.0:
		seek_locomotion("move", t - 5.0, Vector3(0.0, 0.0, -2.3), 1.2, sin(t - 5.0) * 0.35, true)
	elif t < 11.7:
		seek_ability(0, t - 8.0)
	elif t < 15.3:
		seek_ability(1, t - 11.7)
	else:
		seek_death(t - 15.3)

func seek_locomotion(clip: String, time: float, velocity: Vector3, yaw_rate: float,
		yaw: float, slope: bool) -> void:
	_actor.rotation.y = yaw
	_actor.position = Vector3.ZERO
	_floor.rotation.z = 0.055 if slope else 0.0
	_burst_marker.visible = false
	_lob_marker.visible = false
	_projectile.visible = false
	_lob_launch_cached = false
	motion.set_motion(_actor.global_basis * velocity, yaw_rate)
	presentation_label = clip + (" · terrain support" if slope else "")
	_status.text = "Cairn · %s · speed %.2f m/s · turn %.2f rad/s" % [presentation_label, velocity.length(), yaw_rate]
	_seek(clip, time)

func seek_ability(index: int, elapsed: float) -> void:
	_floor.rotation.z = 0.0
	_actor.position = Vector3.ZERO
	_actor.rotation.y = 0.0
	var windup: float = BURST_WINDUP if index == 0 else LOB_WINDUP
	var active_time: float = BURST_ACTIVE if index == 0 else LOB_ACTIVE
	var recovery: float = BURST_RECOVERY if index == 0 else LOB_RECOVERY
	var phase: String = "warning"
	var pose_time: float = 0.65 * clampf(elapsed / windup, 0.0, 1.0)
	if elapsed >= windup:
		phase = "active"
		pose_time = 0.65 + 0.15 * clampf((elapsed - windup) / active_time, 0.0, 1.0)
	if elapsed >= windup + active_time:
		phase = "recovery"
		pose_time = 0.80 + 0.20 * clampf((elapsed - windup - active_time) / recovery, 0.0, 1.0)
	motion.set_motion(Vector3.ZERO, 0.0, 1.0)
	if index == 0:
		_lob_launch_cached = false
	elif not _lob_launch_cached:
		# Sample the authored release pose first. Place the cube above the palm:
		# 0.325 m half-height plus the raised hand's support extent and clearance.
		_seek("attack_1", 0.0)
		var hand_index: int = skeleton.find_bone("hand.R")
		if hand_index < 0:
			hand_index = skeleton.find_bone("hand_R")
		_lob_launch = skeleton.global_transform * skeleton.get_bone_global_pose(hand_index).origin
		_lob_launch += Vector3.UP * 0.55
		_lob_launch_cached = true
	presentation_label = "attack_%d · %s" % [index, phase]
	_status.text = "Cairn · %s · elapsed %.2f s" % [presentation_label, elapsed]
	_burst_marker.visible = index == 0 and elapsed <= windup + active_time
	_lob_marker.visible = index == 1
	_projectile.visible = index == 1 and elapsed < windup
	if _projectile.visible:
		var p: float = clampf(elapsed / windup, 0.0, 1.0)
		_projectile.position = _lob_launch.lerp(Vector3(0.0, 0.3, -4.0), p) + Vector3.UP * (4.0 * 5.0 * p * (1.0 - p))
		_projectile.rotation.y = p * TAU
	_seek("attack_%d" % index, pose_time)

func seek_death(elapsed: float) -> void:
	_floor.rotation.z = 0.0
	_actor.position = Vector3.ZERO
	_actor.rotation.y = 0.0
	_burst_marker.visible = false
	_lob_marker.visible = false
	_projectile.visible = false
	_lob_launch_cached = false
	motion.set_motion(Vector3.ZERO, 0.0, 1.0, true, true)
	presentation_label = "death"
	_status.text = "Cairn · death · full clip, no premature fade · %.2f s" % elapsed
	_seek("death", elapsed)

func _seek(clip: String, time: float) -> void:
	if animation_player.current_animation != clips[clip]:
		# Clear the last skill/death pose for channels absent from the next action.
		# Authored channels are immediately reapplied by seek; no motion is skipped.
		skeleton.reset_bone_poses()
		animation_player.play(clips[clip])
	var animation: Animation = animation_player.get_animation(clips[clip])
	animation_time = fmod(time, animation.length) if clip in ["idle", "move"] else clampf(time, 0.0, animation.length)
	animation_player.seek(animation_time, true)
	animation_player.advance(0.0)
	_capture_authored_articulation()
	skeleton.advance(FIXED_STEP)
	frames_evaluated += 1

func _capture_authored_articulation() -> void:
	latest_authored_articulation_matrices.clear()
	var conversion: Transform3D = Transform3D(Basis(Vector3.RIGHT, Vector3(0.0, 0.0, -1.0), Vector3.UP), Vector3.ZERO)
	var inverse_conversion: Transform3D = conversion.affine_inverse()
	for index: int in range(skeleton.get_bone_count()):
		var bone_name: String = skeleton.get_bone_name(index)
		if bone_name.begins_with("rubble_"):
			continue
		var rest: Transform3D = _bind_skeleton_world * skeleton.get_bone_global_rest(index)
		var pose: Transform3D = skeleton.global_transform * skeleton.get_bone_global_pose(index)
		latest_authored_articulation_matrices[bone_name] = _matrix_rows(inverse_conversion * pose * rest.affine_inverse() * conversion)

func _on_modifier_processed() -> void:
	latest_bone_matrices.clear()
	latest_bone_matrices_godot.clear()
	latest_foot_world.clear()
	# Blender descriptor coordinates [x,y,z] become Godot [x,z,-y].
	# Conjugating maps the evaluated engine deformation back to descriptor axes.
	var coordinate_conversion: Transform3D = Transform3D(Basis(Vector3.RIGHT, Vector3(0.0, 0.0, -1.0), Vector3.UP), Vector3.ZERO)
	var inverse_conversion: Transform3D = coordinate_conversion.affine_inverse()
	for index: int in range(skeleton.get_bone_count()):
		var rest: Transform3D = _bind_skeleton_world * skeleton.get_bone_global_rest(index)
		var posed: Transform3D = skeleton.global_transform * skeleton.get_bone_global_pose(index)
		var matrix: Transform3D = posed * rest.affine_inverse()
		latest_bone_matrices_godot[skeleton.get_bone_name(index)] = _matrix_rows(matrix)
		latest_bone_matrices[skeleton.get_bone_name(index)] = _matrix_rows(inverse_conversion * matrix * coordinate_conversion)
		if skeleton.get_bone_name(index).begins_with("foot"):
			latest_foot_world[skeleton.get_bone_name(index)] = [posed.origin.x, posed.origin.y, posed.origin.z]
	latest_foot_support = motion.last_max_foot_adjustment

func _matrix_rows(matrix: Transform3D) -> Array:
	var rows: Array = [[matrix.basis.x.x, matrix.basis.y.x, matrix.basis.z.x, matrix.origin.x],
		[matrix.basis.x.y, matrix.basis.y.y, matrix.basis.z.y, matrix.origin.y],
		[matrix.basis.x.z, matrix.basis.y.z, matrix.basis.z.z, matrix.origin.z],
		[0.0, 0.0, 0.0, 1.0]]
	for row: Array in rows:
		for column: int in range(4):
			row[column] = snappedf(float(row[column]), 0.0000001)
	return rows

func _build_stage() -> void:
	var environment: WorldEnvironment = WorldEnvironment.new()
	environment.environment = Environment.new()
	environment.environment.background_mode = Environment.BG_COLOR
	environment.environment.background_color = Color(0.11, 0.14, 0.13)
	environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.environment.ambient_light_color = Color(0.76, 0.82, 0.78)
	environment.environment.ambient_light_energy = 0.65
	add_child(environment)
	var light: DirectionalLight3D = DirectionalLight3D.new()
	# Light travels down and toward +Z, illuminating the character's -Z face.
	light.rotation_degrees = Vector3(-52.0, 145.0, 0.0)
	light.light_energy = 1.25
	light.shadow_enabled = true
	add_child(light)
	_floor = StaticBody3D.new()
	_floor.collision_layer = 1
	_floor.collision_mask = 0
	var shape: CollisionShape3D = CollisionShape3D.new()
	var box_shape: BoxShape3D = BoxShape3D.new()
	box_shape.size = Vector3(30.0, 0.2, 30.0)
	shape.shape = box_shape
	shape.position.y = -0.1
	_floor.add_child(shape)
	var ground: MeshInstance3D = MeshInstance3D.new()
	var ground_mesh: BoxMesh = BoxMesh.new()
	ground_mesh.size = box_shape.size
	ground.mesh = ground_mesh
	ground.position.y = -0.1
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = Color(0.24, 0.29, 0.25)
	material.roughness = 1.0
	ground.material_override = material
	_floor.add_child(ground)
	add_child(_floor)
	_actor = Node3D.new()
	_actor.name = "CairnActor"
	add_child(_actor)
	_camera = Camera3D.new()
	_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	_camera.size = 10.5
	_camera.position = Vector3(6.6, 6.0, -9.5)
	add_child(_camera)
	_camera.look_at(Vector3(0.0, 1.65, -0.8), Vector3.UP)
	_camera.current = true
	_burst_marker = _make_ring(4.8, Vector3(0.0, 0.012, 0.0))
	_lob_marker = _make_ring(2.6, Vector3(0.0, 0.014, -4.0))
	_projectile = MeshInstance3D.new()
	var stone_cube: BoxMesh = BoxMesh.new()
	stone_cube.size = Vector3(0.65, 0.65, 0.65)
	_projectile.mesh = stone_cube
	var projectile_material: StandardMaterial3D = StandardMaterial3D.new()
	projectile_material.albedo_color = Color(0.48, 0.50, 0.44)
	projectile_material.roughness = 0.95
	_projectile.material_override = projectile_material
	add_child(_projectile)
	var canvas: CanvasLayer = CanvasLayer.new()
	_status = Label.new()
	_status.position = Vector2(22.0, 18.0)
	_status.add_theme_font_size_override("font_size", 18)
	canvas.add_child(_status)
	add_child(canvas)

func _make_ring(radius: float, position_value: Vector3) -> MeshInstance3D:
	var mesh_instance: MeshInstance3D = MeshInstance3D.new()
	var torus: TorusMesh = TorusMesh.new()
	torus.inner_radius = radius - 0.035
	torus.outer_radius = radius + 0.035
	torus.rings = 64
	torus.ring_segments = 8
	mesh_instance.mesh = torus
	mesh_instance.position = position_value
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.albedo_color = Color(1.0, 0.65, 0.15)
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mesh_instance.material_override = material
	add_child(mesh_instance)
	return mesh_instance
