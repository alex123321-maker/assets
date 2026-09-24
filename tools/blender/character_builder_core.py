"""Core character builder utilities for rigged voxel undead characters in Cube Siege.
Provides:
  - Armature creation with standardized bone hierarchy
  - Voxel part generation and vertex weight assignment
  - Keyframed action generation (idle, move, attack, hit, death)
  - Review camera and lighting setup
  - Multi-view and animation filmstrip rendering
  - GLB export and metrics extraction
"""

from __future__ import annotations
import math
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector, Euler, Matrix

def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def hex_to_linear_rgb(hex_str: str) -> tuple[float, float, float, float]:
    h = hex_str.lstrip("#")
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), 1.0)

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.meshes) + list(bpy.data.materials) + list(bpy.data.cameras) + list(bpy.data.lights) + list(bpy.data.armatures) + list(bpy.data.actions):
        if block.users == 0:
            if isinstance(block, bpy.types.Mesh):
                bpy.data.meshes.remove(block)
            elif isinstance(block, bpy.types.Material):
                bpy.data.materials.remove(block)
            elif isinstance(block, bpy.types.Camera):
                bpy.data.cameras.remove(block)
            elif isinstance(block, bpy.types.Light):
                bpy.data.lights.remove(block)
            elif isinstance(block, bpy.types.Armature):
                bpy.data.armatures.remove(block)
            elif isinstance(block, bpy.types.Action):
                bpy.data.actions.remove(block)

def get_eevee_engine() -> str:
    engine_items = {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    return "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engine_items else "BLENDER_EEVEE"

def create_pbr_material(name: str, color_hex: str, roughness: float = 0.85, metallic: float = 0.0) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = hex_to_linear_rgb(color_hex)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

def add_box_geometry(
    bm: bmesh.types.BMesh,
    center: tuple[float, float, float],
    size: tuple[float, float, float],
    bone_name: str,
    weight_map: dict[str, list[int]],
    mat_index: int = 0,
    rot: tuple[float, float, float] = (0, 0, 0),
):
    cx, cy, cz = center
    dx, dy, dz = [s / 2.0 for s in size]
    
    verts = [
        Vector((-dx, -dy, -dz)), Vector((dx, -dy, -dz)), Vector((dx, dy, -dz)), Vector((-dx, dy, -dz)),
        Vector((-dx, -dy, dz)), Vector((dx, -dy, dz)), Vector((dx, dy, dz)), Vector((-dx, dy, dz)),
    ]
    euler = Euler((math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2])), 'XYZ')
    rot_mat = euler.to_matrix()
    
    transformed_verts = []
    base_idx = len(bm.verts)
    new_indices = []
    for i, v in enumerate(verts):
        tv = rot_mat @ v + Vector((cx, cy, cz))
        bmv = bm.verts.new(tv)
        transformed_verts.append(bmv)
        new_indices.append(base_idx + i)
        
    faces = [
        (0, 1, 2, 3), (4, 7, 6, 5),
        (0, 4, 5, 1), (1, 5, 6, 2),
        (2, 6, 7, 3), (3, 7, 4, 0)
    ]
    for f in faces:
        bmf = bm.faces.new([transformed_verts[i] for i in f])
        bmf.material_index = mat_index
        
    weight_map.setdefault(bone_name, []).extend(new_indices)

def create_armature(name: str, bone_defs: dict[str, dict]) -> bpy.types.Object:
    amt = bpy.data.armatures.new(f"{name}_Armature")
    amt_obj = bpy.data.objects.new(name, amt)
    bpy.context.collection.objects.link(amt_obj)
    bpy.context.view_layer.objects.active = amt_obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    edit_bones = amt.edit_bones
    for b_name, b_info in bone_defs.items():
        eb = edit_bones.new(b_name)
        eb.head = Vector(b_info["head"])
        eb.tail = Vector(b_info["tail"])
        if "roll" in b_info:
            eb.roll = math.radians(b_info["roll"])
            
    for b_name, b_info in bone_defs.items():
        parent_name = b_info.get("parent")
        if parent_name and parent_name in edit_bones:
            edit_bones[b_name].parent = edit_bones[parent_name]
            edit_bones[b_name].use_connect = b_info.get("connected", False)
            
    bpy.ops.object.mode_set(mode='OBJECT')
    return amt_obj

def bind_mesh_to_armature(
    mesh_obj: bpy.types.Object,
    amt_obj: bpy.types.Object,
    weight_map: dict[str, list[int]],
):
    mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = amt_obj
    mod.use_vertex_groups = True
    
    for bone_name, vert_indices in weight_map.items():
        vg = mesh_obj.vertex_groups.new(name=bone_name)
        vg.add(vert_indices, 1.0, 'REPLACE')
        
    mesh_obj.parent = amt_obj

def setup_lights():
    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = 4.2
    sun_data.color = (1.0, 0.98, 0.94)
    if hasattr(sun_data, "use_shadow_jitter"):
        sun_data.use_shadow_jitter = False
    if hasattr(sun_data, "shadow_filter_radius"):
        sun_data.shadow_filter_radius = 0.0
    sun = bpy.data.objects.new("Sun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.location = (15, -20, 20)
    sun.rotation_euler = (math.radians(50), math.radians(15), math.radians(-35))
    
    fill_data = bpy.data.lights.new("Fill", type="SUN")
    fill_data.energy = 1.6
    fill_data.color = (0.75, 0.85, 1.0)
    fill_data.use_shadow = False
    if hasattr(fill_data, "use_shadow_jitter"):
        fill_data.use_shadow_jitter = False
    fill = bpy.data.objects.new("Fill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.rotation_euler = (math.radians(-30), math.radians(-40), math.radians(120))

def add_ground_plane(size: float = 30.0) -> bpy.types.Object:
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    mat = create_pbr_material("mat_ground", "#6f8872", roughness=0.95) # Stylized grass tone
    ground.data.materials.append(mat)
    return ground

def look_at(obj: bpy.types.Object, target: Vector):
    dir_vec = target - obj.location
    obj.rotation_euler = dir_vec.to_track_quat("-Z", "Y").to_euler()
