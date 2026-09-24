"""Build and render 3D blockout candidates for the Zombie enemy and the core enemy family lineup.
Compares:
  Variant A: Standard Symmetrical Shambler
  Variant B: Hunched Decay Stalker (hunched forward spine, reaching claw arms)
  Variant C: Feral Low-slung Shambler

Also builds a Family Lineup blockout:
  [Hero Proxy (1.8m)] vs [Zombie B (1.8m)] vs [Ranged Skirmisher (1.8m slender + bow)] vs [Siege Breaker (2.4m massive brute)]

Outputs:
  assets/characters/zombie/review/zombie_blockout_comparison.png
  assets/characters/zombie/review/zombie_blockout_silhouette.png
  assets/characters/zombie/review/blockout_lineup.png
  assets/characters/zombie/review/blockout_gameplay_camera.png
"""

from __future__ import annotations
import math
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector, Euler

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "assets" / "characters" / "zombie" / "review"

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.meshes) + list(bpy.data.materials) + list(bpy.data.cameras) + list(bpy.data.lights) + list(bpy.data.armatures):
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

def create_mat(name: str, color: tuple[float, float, float, float], roughness: float = 0.8, metallic: float = 0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

def add_box(bm, center: tuple[float, float, float], size: tuple[float, float, float], rot: tuple[float, float, float] = (0, 0, 0)):
    cx, cy, cz = center
    dx, dy, dz = [s / 2.0 for s in size]
    
    verts = [
        Vector((-dx, -dy, -dz)), Vector((dx, -dy, -dz)), Vector((dx, dy, -dz)), Vector((-dx, dy, -dz)),
        Vector((-dx, -dy, dz)), Vector((dx, -dy, dz)), Vector((dx, dy, dz)), Vector((-dx, dy, dz)),
    ]
    euler = Euler((math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2])), 'XYZ')
    rot_mat = euler.to_matrix()
    
    transformed_verts = []
    for v in verts:
        tv = rot_mat @ v + Vector((cx, cy, cz))
        transformed_verts.append(bm.verts.new(tv))
        
    faces = [
        (0, 1, 2, 3), (4, 7, 6, 5),
        (0, 4, 5, 1), (1, 5, 6, 2),
        (2, 6, 7, 3), (3, 7, 4, 0)
    ]
    for f in faces:
        bm.faces.new([transformed_verts[i] for i in f])

def build_variant_a(offset_x: float) -> bpy.types.Object:
    bm = bmesh.new()
    add_box(bm, (offset_x - 0.15, 0.0, 0.08), (0.2, 0.35, 0.16))
    add_box(bm, (offset_x + 0.15, 0.0, 0.08), (0.2, 0.35, 0.16))
    add_box(bm, (offset_x - 0.15, 0.0, 0.35), (0.2, 0.22, 0.40))
    add_box(bm, (offset_x + 0.15, 0.0, 0.35), (0.2, 0.22, 0.40))
    add_box(bm, (offset_x - 0.15, 0.0, 0.75), (0.22, 0.24, 0.42))
    add_box(bm, (offset_x + 0.15, 0.0, 0.75), (0.22, 0.24, 0.42))
    add_box(bm, (offset_x, 0.0, 1.02), (0.50, 0.28, 0.18))
    add_box(bm, (offset_x, 0.0, 1.25), (0.54, 0.32, 0.38))
    add_box(bm, (offset_x, 0.02, 1.48), (0.22, 0.22, 0.14))
    add_box(bm, (offset_x, 0.04, 1.68), (0.42, 0.42, 0.40))
    add_box(bm, (offset_x - 0.38, 0.08, 1.28), (0.18, 0.20, 0.36), (20, 0, 0))
    add_box(bm, (offset_x + 0.38, 0.08, 1.28), (0.18, 0.20, 0.36), (20, 0, 0))
    add_box(bm, (offset_x - 0.38, 0.32, 1.15), (0.18, 0.36, 0.18), (60, 0, 0))
    add_box(bm, (offset_x + 0.38, 0.32, 1.15), (0.18, 0.36, 0.18), (60, 0, 0))
    mesh = bpy.data.meshes.new("Zombie_VarA_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("Zombie_VarA", mesh)
    bpy.context.collection.objects.link(obj)
    return obj

def build_variant_b(offset_x: float) -> bpy.types.Object:
    bm = bmesh.new()
    add_box(bm, (offset_x - 0.18, 0.08, 0.07), (0.22, 0.38, 0.14))
    add_box(bm, (offset_x + 0.18, -0.06, 0.07), (0.22, 0.38, 0.14))
    add_box(bm, (offset_x - 0.18, 0.04, 0.32), (0.20, 0.22, 0.38), (-8, 0, 0))
    add_box(bm, (offset_x + 0.18, -0.04, 0.32), (0.20, 0.22, 0.38), (6, 0, 0))
    add_box(bm, (offset_x - 0.18, -0.02, 0.70), (0.22, 0.24, 0.42), (12, 0, 0))
    add_box(bm, (offset_x + 0.18, -0.08, 0.70), (0.22, 0.24, 0.42), (-4, 0, 0))
    add_box(bm, (offset_x, -0.04, 0.96), (0.52, 0.30, 0.20), (14, 0, 0))
    add_box(bm, (offset_x - 0.12, 0.10, 0.88), (0.16, 0.08, 0.24), (16, 5, 0))
    add_box(bm, (offset_x + 0.10, 0.10, 0.86), (0.18, 0.08, 0.28), (12, -4, 0))
    add_box(bm, (offset_x, -0.16, 0.88), (0.42, 0.08, 0.22), (10, 0, 0))
    add_box(bm, (offset_x, 0.08, 1.20), (0.54, 0.36, 0.38), (22, 2, -2))
    add_box(bm, (offset_x - 0.22, 0.14, 1.34), (0.20, 0.26, 0.16), (20, 10, -5))
    add_box(bm, (offset_x + 0.22, 0.12, 1.30), (0.18, 0.24, 0.14), (24, -8, 4))
    add_box(bm, (offset_x, 0.22, 1.40), (0.22, 0.22, 0.16), (30, 0, 0))
    add_box(bm, (offset_x, 0.34, 1.56), (0.42, 0.44, 0.40), (14, 0, 0))
    add_box(bm, (offset_x, 0.44, 1.44), (0.34, 0.24, 0.16), (8, 0, 0))
    add_box(bm, (offset_x - 0.10, 0.54, 1.62), (0.10, 0.06, 0.10), (14, 0, 0))
    add_box(bm, (offset_x + 0.10, 0.54, 1.62), (0.10, 0.06, 0.10), (14, 0, 0))
    add_box(bm, (offset_x - 0.38, 0.18, 1.24), (0.18, 0.22, 0.38), (35, 5, -8))
    add_box(bm, (offset_x - 0.38, 0.48, 1.22), (0.18, 0.42, 0.18), (65, 0, -10))
    add_box(bm, (offset_x - 0.38, 0.74, 1.20), (0.20, 0.16, 0.14), (45, 0, -10))
    add_box(bm, (offset_x - 0.42, 0.85, 1.18), (0.06, 0.14, 0.06), (30, 10, -5))
    add_box(bm, (offset_x - 0.35, 0.86, 1.20), (0.06, 0.15, 0.06), (35, 0, -8))
    add_box(bm, (offset_x + 0.38, 0.14, 1.20), (0.18, 0.22, 0.38), (28, -8, 6))
    add_box(bm, (offset_x + 0.38, 0.42, 1.08), (0.18, 0.40, 0.18), (55, 0, 8))
    add_box(bm, (offset_x + 0.38, 0.66, 1.02), (0.20, 0.16, 0.14), (35, 0, 8))
    add_box(bm, (offset_x + 0.42, 0.76, 1.00), (0.06, 0.14, 0.06), (25, -10, 5))
    add_box(bm, (offset_x + 0.35, 0.77, 1.01), (0.06, 0.15, 0.06), (30, 0, 8))
    mesh = bpy.data.meshes.new("Zombie_VarB_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("Zombie_VarB", mesh)
    bpy.context.collection.objects.link(obj)
    return obj

def build_variant_c(offset_x: float) -> bpy.types.Object:
    bm = bmesh.new()
    add_box(bm, (offset_x - 0.26, 0.0, 0.08), (0.24, 0.40, 0.16))
    add_box(bm, (offset_x + 0.22, 0.05, 0.08), (0.24, 0.40, 0.16))
    add_box(bm, (offset_x - 0.24, -0.02, 0.32), (0.22, 0.24, 0.38), (8, 6, 0))
    add_box(bm, (offset_x + 0.20, 0.02, 0.32), (0.22, 0.24, 0.38), (-6, -6, 0))
    add_box(bm, (offset_x - 0.20, -0.04, 0.68), (0.26, 0.26, 0.40), (-6, 4, 0))
    add_box(bm, (offset_x + 0.18, -0.02, 0.68), (0.26, 0.26, 0.40), (8, -4, 0))
    add_box(bm, (offset_x, -0.04, 0.94), (0.60, 0.34, 0.22))
    add_box(bm, (offset_x - 0.02, 0.06, 1.18), (0.64, 0.42, 0.42), (20, 0, -4))
    add_box(bm, (offset_x, 0.24, 1.38), (0.46, 0.44, 0.42), (18, 0, 0))
    add_box(bm, (offset_x - 0.46, 0.06, 1.12), (0.22, 0.24, 0.42), (10, 10, 0))
    add_box(bm, (offset_x - 0.46, 0.20, 0.78), (0.20, 0.22, 0.44), (20, 5, 0))
    add_box(bm, (offset_x - 0.46, 0.26, 0.50), (0.24, 0.26, 0.20))
    add_box(bm, (offset_x + 0.44, 0.14, 1.14), (0.22, 0.24, 0.40), (30, -10, 0))
    add_box(bm, (offset_x + 0.44, 0.44, 1.00), (0.20, 0.38, 0.20), (60, 0, 0))
    add_box(bm, (offset_x + 0.44, 0.66, 0.92), (0.24, 0.24, 0.20))
    mesh = bpy.data.meshes.new("Zombie_VarC_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("Zombie_VarC", mesh)
    bpy.context.collection.objects.link(obj)
    return obj

def build_hero_proxy(offset_x: float) -> bpy.types.Object:
    # 0.8 x 1.8 x 0.8 warrior hero proxy
    bm = bmesh.new()
    # Boots
    add_box(bm, (offset_x - 0.18, 0.0, 0.10), (0.22, 0.36, 0.20))
    add_box(bm, (offset_x + 0.18, 0.0, 0.10), (0.22, 0.36, 0.20))
    # Greaves / Legs
    add_box(bm, (offset_x - 0.18, 0.0, 0.50), (0.22, 0.24, 0.60))
    add_box(bm, (offset_x + 0.18, 0.0, 0.50), (0.22, 0.24, 0.60))
    # Belt / Pelvis
    add_box(bm, (offset_x, 0.0, 0.92), (0.54, 0.32, 0.22))
    # Chestplate
    add_box(bm, (offset_x, 0.0, 1.25), (0.58, 0.36, 0.44))
    # Pauldrons
    add_box(bm, (offset_x - 0.38, 0.0, 1.42), (0.22, 0.28, 0.20))
    add_box(bm, (offset_x + 0.38, 0.0, 1.42), (0.22, 0.28, 0.20))
    # Head & Helmet
    add_box(bm, (offset_x, 0.0, 1.62), (0.44, 0.44, 0.40))
    add_box(bm, (offset_x, 0.0, 1.82), (0.16, 0.42, 0.10)) # Crest
    # Sword (Right hand)
    add_box(bm, (offset_x + 0.44, 0.20, 0.85), (0.14, 0.14, 0.16)) # Hand
    add_box(bm, (offset_x + 0.44, 0.24, 1.15), (0.06, 0.12, 0.70)) # Blade
    # Shield (Left arm)
    add_box(bm, (offset_x - 0.48, 0.10, 1.10), (0.12, 0.44, 0.60))
    
    mesh = bpy.data.meshes.new("HeroProxy_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("HeroProxy", mesh)
    bpy.context.collection.objects.link(obj)
    return obj

def build_skirmisher_blockout(offset_x: float) -> bpy.types.Object:
    # Lean, slender undead skeleton archer (~1.8m tall, 0.6 x 1.8 x 0.6 collision)
    bm = bmesh.new()
    # Slender bone feet
    add_box(bm, (offset_x - 0.14, 0.04, 0.06), (0.14, 0.30, 0.12))
    add_box(bm, (offset_x + 0.14, -0.04, 0.06), (0.14, 0.30, 0.12))
    # Bone shins
    add_box(bm, (offset_x - 0.14, 0.02, 0.34), (0.12, 0.14, 0.44))
    add_box(bm, (offset_x + 0.14, -0.02, 0.34), (0.12, 0.14, 0.44))
    # Bone thighs
    add_box(bm, (offset_x - 0.13, 0.0, 0.72), (0.14, 0.16, 0.44))
    add_box(bm, (offset_x + 0.13, 0.0, 0.72), (0.14, 0.16, 0.44))
    # Pelvis
    add_box(bm, (offset_x, 0.0, 0.98), (0.38, 0.22, 0.16))
    # Slender spine / ribcage (distinct negative space around ribs)
    add_box(bm, (offset_x, 0.0, 1.12), (0.16, 0.16, 0.18)) # lower spine
    add_box(bm, (offset_x, 0.02, 1.28), (0.42, 0.24, 0.26)) # ribcage
    # Ragged quiver on back
    add_box(bm, (offset_x + 0.10, -0.16, 1.30), (0.14, 0.14, 0.55), (15, -15, 0))
    # Arrow fletchings sticking out
    add_box(bm, (offset_x + 0.15, -0.22, 1.62), (0.08, 0.08, 0.16), (15, -15, 0))
    # Neck & Skull
    add_box(bm, (offset_x, 0.02, 1.46), (0.14, 0.14, 0.12))
    add_box(bm, (offset_x, 0.04, 1.64), (0.36, 0.38, 0.36))
    # Eye sockets
    add_box(bm, (offset_x - 0.08, 0.22, 1.66), (0.08, 0.04, 0.08))
    add_box(bm, (offset_x + 0.08, 0.22, 1.66), (0.08, 0.04, 0.08))
    # Left arm holding Bow forward
    add_box(bm, (offset_x - 0.28, 0.04, 1.32), (0.12, 0.14, 0.34), (20, 10, 0))
    add_box(bm, (offset_x - 0.28, 0.30, 1.28), (0.12, 0.34, 0.12), (75, 0, 0))
    add_box(bm, (offset_x - 0.28, 0.48, 1.28), (0.14, 0.12, 0.12)) # Left hand
    # Recurve Bow (stepped voxel arc in left hand)
    add_box(bm, (offset_x - 0.32, 0.48, 1.28), (0.08, 0.10, 0.26))
    add_box(bm, (offset_x - 0.32, 0.44, 1.48), (0.08, 0.08, 0.22), (-15, 0, 0))
    add_box(bm, (offset_x - 0.32, 0.44, 1.08), (0.08, 0.08, 0.22), (15, 0, 0))
    add_box(bm, (offset_x - 0.32, 0.38, 1.64), (0.06, 0.08, 0.16), (-30, 0, 0))
    add_box(bm, (offset_x - 0.32, 0.38, 0.92), (0.06, 0.08, 0.16), (30, 0, 0))
    # Right arm pulled back ready to draw
    add_box(bm, (offset_x + 0.28, 0.02, 1.30), (0.12, 0.14, 0.34), (10, -10, 0))
    add_box(bm, (offset_x + 0.28, 0.12, 1.10), (0.12, 0.24, 0.12), (30, 0, 0))
    
    mesh = bpy.data.meshes.new("SkirmisherBlockout_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("SkirmisherBlockout", mesh)
    bpy.context.collection.objects.link(obj)
    return obj

def build_siege_breaker_blockout(offset_x: float) -> bpy.types.Object:
    # Huge, wide undead siege brute (~2.4m tall, 1.4 x 2.4 x 1.4 collision)
    bm = bmesh.new()
    # Massive blocky feet / stone boots
    add_box(bm, (offset_x - 0.40, 0.08, 0.14), (0.42, 0.60, 0.28))
    add_box(bm, (offset_x + 0.40, -0.06, 0.14), (0.42, 0.60, 0.28))
    # Heavy armored shins
    add_box(bm, (offset_x - 0.38, 0.04, 0.50), (0.40, 0.42, 0.52))
    add_box(bm, (offset_x + 0.38, -0.04, 0.50), (0.40, 0.42, 0.52))
    # Massive thighs
    add_box(bm, (offset_x - 0.34, 0.0, 0.95), (0.44, 0.44, 0.50))
    add_box(bm, (offset_x + 0.34, 0.0, 0.95), (0.44, 0.44, 0.50))
    # Massive heavy pelvis & loinplate
    add_box(bm, (offset_x, 0.0, 1.30), (1.00, 0.62, 0.34))
    add_box(bm, (offset_x, 0.28, 1.15), (0.44, 0.12, 0.48), (10, 0, 0)) # Loincloth
    # Giant muscular/corrupted torso
    add_box(bm, (offset_x, 0.06, 1.68), (1.20, 0.74, 0.56), (12, 0, 0))
    # Reinforced stone/iron spine & back plates
    add_box(bm, (offset_x, -0.32, 1.76), (0.64, 0.20, 0.50), (12, 0, 0))
    # Massive shoulder pauldrons
    add_box(bm, (offset_x - 0.78, 0.08, 1.95), (0.46, 0.54, 0.42), (10, 15, -5))
    add_box(bm, (offset_x + 0.78, 0.08, 1.95), (0.46, 0.54, 0.42), (10, -15, 5))
    # Heavy neck & massive skull with iron jaw
    add_box(bm, (offset_x, 0.22, 1.92), (0.44, 0.42, 0.26))
    add_box(bm, (offset_x, 0.28, 2.18), (0.62, 0.60, 0.52), (10, 0, 0))
    add_box(bm, (offset_x, 0.48, 2.06), (0.50, 0.34, 0.26)) # Heavy battering jaw
    # Massive Battering Arms & Stone Gauntlets
    # Left Arm
    add_box(bm, (offset_x - 0.82, 0.14, 1.62), (0.40, 0.42, 0.50), (25, 10, 0))
    add_box(bm, (offset_x - 0.84, 0.46, 1.30), (0.42, 0.56, 0.42), (55, 5, 0))
    # Left Giant Battering Fist (Huge stone/iron gauntlet)
    add_box(bm, (offset_x - 0.84, 0.78, 1.08), (0.52, 0.54, 0.50), (35, 5, 0))
    # Right Arm
    add_box(bm, (offset_x + 0.82, 0.10, 1.60), (0.40, 0.42, 0.50), (20, -10, 0))
    add_box(bm, (offset_x + 0.84, 0.42, 1.28), (0.42, 0.54, 0.42), (50, -5, 0))
    # Right Giant Battering Fist
    add_box(bm, (offset_x + 0.84, 0.74, 1.05), (0.52, 0.54, 0.50), (30, -5, 0))
    
    mesh = bpy.data.meshes.new("SiegeBreakerBlockout_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("SiegeBreakerBlockout", mesh)
    bpy.context.collection.objects.link(obj)
    return obj

def setup_lights():
    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = 4.2
    sun_data.color = (1.0, 0.98, 0.94)
    sun = bpy.data.objects.new("Sun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.location = (15, -20, 20)
    sun.rotation_euler = (math.radians(50), math.radians(15), math.radians(-35))
    
    fill_data = bpy.data.lights.new("Fill", type="SUN")
    fill_data.energy = 1.6
    fill_data.color = (0.75, 0.85, 1.0)
    fill = bpy.data.objects.new("Fill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.rotation_euler = (math.radians(-30), math.radians(-40), math.radians(120))

def run_renders():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    engine_items = {item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    eevee_engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engine_items else "BLENDER_EEVEE"
    
    # -------------------------------------------------------------
    # 1. Zombie 3 Variants Comparison & Silhouette
    # -------------------------------------------------------------
    clear_scene()
    mat_flesh = create_mat("mat_zombie_flesh", (0.42, 0.52, 0.34, 1.0), roughness=0.85)
    mat_black = create_mat("mat_black", (0.01, 0.01, 0.01, 1.0), roughness=1.0)
    
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    mat_ground = create_mat("mat_ground", (0.80, 0.82, 0.85, 1.0), roughness=0.95)
    ground.data.materials.append(mat_ground)
    
    obj_a = build_variant_a(offset_x=-1.6)
    obj_b = build_variant_b(offset_x=0.0)
    obj_c = build_variant_c(offset_x=1.6)
    
    for obj in [obj_a, obj_b, obj_c]:
        obj.data.materials.append(mat_flesh)
        
    setup_lights()
    
    cam_data = bpy.data.cameras.new("FrontCam")
    cam = bpy.data.objects.new("FrontCam", cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 4.6
    cam.location = (0, -6.0, 0.95)
    cam.rotation_euler = (math.radians(90), 0, 0)
    
    scene = bpy.context.scene
    scene.render.engine = eevee_engine
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 640
    scene.render.image_settings.file_format = "PNG"
    
    scene.render.filepath = str((OUTPUT_DIR / "zombie_blockout_comparison.png").resolve())
    bpy.ops.render.render(write_still=True)
    print("Rendered zombie_blockout_comparison.png")
    
    # Silhouette render
    for obj in [obj_a, obj_b, obj_c]:
        obj.data.materials.clear()
        obj.data.materials.append(mat_black)
    ground.hide_render = True
    scene.world.color = (1.0, 1.0, 1.0)
    
    scene.render.filepath = str((OUTPUT_DIR / "zombie_blockout_silhouette.png").resolve())
    bpy.ops.render.render(write_still=True)
    print("Rendered zombie_blockout_silhouette.png")
    
    # -------------------------------------------------------------
    # 2. Family Lineup Blockout: Hero, Zombie B, Archer, Siege Breaker
    # -------------------------------------------------------------
    clear_scene()
    ground = bpy.data.objects.new("GroundPlane", bpy.data.meshes.new("GroundPlane"))
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    ground = bpy.context.active_object
    mat_ground = create_mat("mat_ground", (0.78, 0.80, 0.82, 1.0), roughness=0.95)
    ground.data.materials.append(mat_ground)
    ground.hide_render = False
    
    mat_hero = create_mat("mat_hero", (0.22, 0.45, 0.75, 1.0), roughness=0.6, metallic=0.2)
    mat_zombie = create_mat("mat_zombie", (0.42, 0.52, 0.34, 1.0), roughness=0.85)
    mat_skirm = create_mat("mat_skirm", (0.84, 0.82, 0.74, 1.0), roughness=0.75)
    mat_breaker = create_mat("mat_breaker", (0.36, 0.34, 0.38, 1.0), roughness=0.95)
    
    # Line up from left to right: Hero (-2.7), Zombie (-0.9), Skirmisher (+0.8), Siege Breaker (+2.9)
    hero_obj = build_hero_proxy(offset_x=-2.7)
    hero_obj.data.materials.append(mat_hero)
    
    zomb_obj = build_variant_b(offset_x=-0.9)
    zomb_obj.data.materials.append(mat_zombie)
    
    skirm_obj = build_skirmisher_blockout(offset_x=0.8)
    skirm_obj.data.materials.append(mat_skirm)
    
    breaker_obj = build_siege_breaker_blockout(offset_x=2.9)
    breaker_obj.data.materials.append(mat_breaker)
    
    setup_lights()
    
    cam_data = bpy.data.cameras.new("LineupCam")
    cam = bpy.data.objects.new("LineupCam", cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    
    # Front lineup view
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 8.5
    cam.location = (0.2, -8.0, 1.25)
    cam.rotation_euler = (math.radians(88), 0, 0)
    
    scene.world.color = (0.88, 0.90, 0.92)
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 800
    scene.render.filepath = str((OUTPUT_DIR / "blockout_lineup.png").resolve())
    bpy.ops.render.render(write_still=True)
    print("Rendered blockout_lineup.png")
    
    # Game camera view (Godot CameraMath: FOV 45, angle (15, 20, 15))
    cam.data.type = "PERSP"
    cam.data.angle = math.radians(45.0)
    center_focus = Vector((0.2, 0.0, 1.0))
    # Offset scaled for viewing all 4 characters
    cam_offset = Vector((10.0, -10.0, 13.33)) # 45 deg azimuth, 43.3 deg elevation
    cam.location = center_focus + cam_offset
    dir_vec = center_focus - cam.location
    cam.rotation_euler = dir_vec.to_track_quat("-Z", "Y").to_euler()
    
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.filepath = str((OUTPUT_DIR / "blockout_gameplay_camera.png").resolve())
    bpy.ops.render.render(write_still=True)
    print("Rendered blockout_gameplay_camera.png")

if __name__ == "__main__":
    run_renders()
