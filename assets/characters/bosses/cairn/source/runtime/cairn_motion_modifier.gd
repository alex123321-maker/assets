extends SkeletonModifier3D
class_name CairnMotionModifier

## Additive presentation only. The owner supplies collision-resolved velocity;
## this modifier never moves its gameplay body or controls attack/death timing.
## Godot 4.6 applies this after authored animation and restores input poses.
@export var reference_speed: float = 2.3
@export var response: float = 7.0
@export var body_yaw_amplitude: float = 0.016
@export var turn_secondary_yaw: float = 0.022
@export var body_sway: float = 0.010
@export var foot_support_enabled: bool = true
@export var foot_sole_offset: float = 0.15
@export var max_foot_correction: float = 0.12
@export var ground_ray_height: float = 0.45
@export var ground_ray_depth: float = 0.75
@export_flags_3d_physics var ground_collision_mask: int = 1

var world_velocity: Vector3 = Vector3.ZERO
var turn_rate: float = 0.0
var action_weight: float = 0.0
var grounded: bool = true
var dying: bool = false
var modification_count: int = 0
var support_adjustment_count: int = 0
var last_max_foot_adjustment: float = 0.0
var last_motion_rotation: Vector3 = Vector3.ZERO
var _velocity: Vector3 = Vector3.ZERO
var _turn: float = 0.0
var _clock: float = 0.0
var _root: int = -1
var _thighs: PackedInt32Array = PackedInt32Array()
var _shins: PackedInt32Array = PackedInt32Array()
var _feet: PackedInt32Array = PackedInt32Array()

func set_motion(velocity: Vector3, yaw_rate: float, ability_weight: float = 0.0,
		is_grounded: bool = true, is_dying: bool = false) -> void:
	world_velocity = velocity
	turn_rate = yaw_rate
	action_weight = clampf(ability_weight, 0.0, 1.0)
	grounded = is_grounded
	dying = is_dying

func _validate_bone_names() -> void:
	var skeleton: Skeleton3D = get_skeleton()
	if not skeleton:
		return
	_root = skeleton.find_bone("root")
	_thighs = PackedInt32Array([_bone(skeleton, "thigh.L"), _bone(skeleton, "thigh.R")])
	_shins = PackedInt32Array([_bone(skeleton, "shin.L"), _bone(skeleton, "shin.R")])
	_feet = PackedInt32Array([_bone(skeleton, "foot.L"), _bone(skeleton, "foot.R")])

func _bone(skeleton: Skeleton3D, bone_name: String) -> int:
	var index: int = skeleton.find_bone(bone_name)
	return index if index >= 0 else skeleton.find_bone(bone_name.replace(".", "_"))

func _process_modification_with_delta(delta: float) -> void:
	var skeleton: Skeleton3D = get_skeleton()
	if not skeleton or dying:
		return
	if _root < 0 or _feet.size() != 2:
		_validate_bone_names()
	var blend: float = 1.0 - exp(-response * maxf(delta, 0.0))
	_velocity = _velocity.lerp(world_velocity, blend)
	_turn = lerpf(_turn, turn_rate, blend)
	_clock += maxf(delta, 0.0)
	var weight: float = 1.0 - action_weight
	var local_velocity: Vector3 = skeleton.global_basis.orthonormalized().inverse() * _velocity
	var speed_weight: float = clampf(Vector2(local_velocity.x, local_velocity.z).length() / maxf(reference_speed, 0.01), 0.0, 1.35)
	var turn_weight: float = clampf(_turn / 2.4, -1.0, 1.0)
	var secondary_yaw: float = (sin(_clock * 4.6) * body_yaw_amplitude + turn_weight * turn_secondary_yaw) * speed_weight * weight
	last_motion_rotation = Vector3(0.0, secondary_yaw, 0.0)
	last_max_foot_adjustment = 0.0
	if weight > 0.001:
		if _root >= 0:
			# Whole-body yaw/sway preserves authored pelvis, neckline and hand/leg
			# clearances. Independent torso lean would close those cube interfaces.
			var root_pose: Transform3D = skeleton.get_bone_global_pose(_root)
			root_pose.basis = Basis(Vector3.UP, secondary_yaw) * root_pose.basis
			root_pose.origin.x += (cos(_clock * 4.6) + turn_weight) * body_sway * speed_weight * weight
			skeleton.set_bone_global_pose(_root, root_pose)
		if grounded and foot_support_enabled:
			for side: int in range(2):
				_support_foot(skeleton, side, weight)
	modification_count += 1

func _support_foot(skeleton: Skeleton3D, side: int, weight: float) -> void:
	var thigh: int = _thighs[side]
	var shin: int = _shins[side]
	var foot: int = _feet[side]
	if thigh < 0 or shin < 0 or foot < 0 or not is_inside_tree():
		return
	var foot_pose: Transform3D = skeleton.get_bone_global_pose(foot)
	var foot_world: Vector3 = skeleton.global_transform * foot_pose.origin
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(
		foot_world + Vector3.UP * ground_ray_height,
		foot_world - Vector3.UP * ground_ray_depth, ground_collision_mask)
	var hit: Dictionary = get_world_3d().direct_space_state.intersect_ray(query)
	if hit.is_empty():
		return
	var contact: Vector3 = hit["position"]
	var desired_height: float = contact.y + foot_sole_offset
	# Only stance feet get support. A raised swinging foot retains its authored arc.
	if foot_world.y - desired_height > 0.07:
		return
	var lift: float = clampf(desired_height - foot_world.y, 0.0, max_foot_correction) * weight
	if lift < 0.0001:
		return
	var goal: Vector3 = skeleton.global_transform.affine_inverse() * (foot_world + Vector3.UP * lift)
	_solve_leg(skeleton, thigh, shin, foot, goal)
	last_max_foot_adjustment = maxf(last_max_foot_adjustment, lift)
	support_adjustment_count += 1

func _solve_leg(skeleton: Skeleton3D, thigh: int, shin: int, foot: int, goal: Vector3) -> void:
	var upper: Transform3D = skeleton.get_bone_global_pose(thigh)
	var lower: Transform3D = skeleton.get_bone_global_pose(shin)
	var ankle: Transform3D = skeleton.get_bone_global_pose(foot)
	var a: Vector3 = upper.origin
	var b: Vector3 = lower.origin
	var c: Vector3 = ankle.origin
	var root_deformation: Basis = skeleton.get_bone_global_pose(_root).basis * skeleton.get_bone_global_rest(_root).basis.inverse()
	var right: Vector3 = (root_deformation * Vector3.RIGHT).normalized()
	var forward: Vector3 = (root_deformation * Vector3.FORWARD).normalized()
	var upper_lateral: float = (b - a).dot(right)
	var ankle_lateral: float = (c - a).dot(right)
	# The authored hinges rotate about X. Preserve their lateral offsets instead
	# of introducing a 3D knee-plane rotation that wedges neighboring whole cubes.
	var upper_vector: Vector3 = (b - a) - right * upper_lateral
	var lower_vector: Vector3 = (c - b) - right * (c - b).dot(right)
	var upper_length: float = upper_vector.length()
	var lower_length: float = lower_vector.length()
	if upper_length < 0.001 or lower_length < 0.001:
		return
	goal += right * (ankle_lateral - (goal - a).dot(right))
	var planar_goal: Vector3 = (goal - a) - right * ankle_lateral
	var direction: Vector3 = planar_goal.normalized()
	var distance: float = clampf(planar_goal.length(), absf(upper_length - lower_length) + 0.000001, upper_length + lower_length)
	goal = a + direction * distance + right * ankle_lateral
	var bend: Vector3 = upper_vector - direction * upper_vector.dot(direction)
	if bend.length_squared() < 0.00001:
		bend = forward - direction * forward.dot(direction)
	if bend.length_squared() < 0.00001:
		return
	bend = bend.normalized()
	var along: float = (upper_length * upper_length - lower_length * lower_length + distance * distance) / (2.0 * distance)
	var height: float = sqrt(maxf(0.0, upper_length * upper_length - along * along))
	var knee: Vector3 = a + direction * along + bend * height + right * upper_lateral
	var upper_angle: float = upper_vector.signed_angle_to((knee - a) - right * upper_lateral, right)
	upper.basis = Basis(right, upper_angle) * upper.basis
	skeleton.set_bone_global_pose(thigh, upper)
	lower.origin = knee
	var lower_angle: float = lower_vector.signed_angle_to((goal - knee) - right * (goal - knee).dot(right), right)
	lower.basis = Basis(right, lower_angle) * lower.basis
	skeleton.set_bone_global_pose(shin, lower)
	# Preserve the animated foot orientation while solving its support position.
	ankle.origin = goal
	skeleton.set_bone_global_pose(foot, ankle)
