"""Geometry and reproducible review scene shared by authoring and source-only build."""
from __future__ import annotations
import math
from pathlib import Path
import bpy
from mathutils import Vector
from model_data import blender_center
from canonical_png import remove_render_metadata


def reproducible_renderer(scene):
    # EEVEE accumulation varies by a few 8-bit values across fresh processes.
    # Fixed-seed CPU path tracing retains the authored PBR/vertex materials.
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU'; scene.cycles.samples=64
    scene.cycles.use_adaptive_sampling=False; scene.cycles.use_denoising=False
    scene.cycles.seed=0; scene.cycles.use_animated_seed=False
    scene.render.threads_mode='FIXED'; scene.render.threads=8


def linear(h):
    values=[int(h.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values)+(1.0,)


def material(name,metallic=0,emission=0):
    mat=bpy.data.materials.new(name); mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF')
    color=mat.node_tree.nodes.new('ShaderNodeVertexColor'); color.layer_name='VoxelColor'
    mat.node_tree.links.new(color.outputs['Color'],bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value=.88 if not metallic else .65
    bs.inputs['Metallic'].default_value=metallic
    if emission:
        mat.node_tree.links.new(color.outputs['Color'],bs.inputs['Emission Color'])
        bs.inputs['Emission Strength'].default_value=emission
    return mat


def create_mesh(spec,cells,assignments,armature=None,grey=False):
    step=spec['voxel_size_m']; vertices=[]; polygons=[]; colors=[]; groups={}; slots=[]
    faces=[((-1,0,0),[(0,0,0),(0,0,1),(0,1,1),(0,1,0)]),
           ((1,0,0),[(1,0,0),(1,1,0),(1,1,1),(1,0,1)]),
           ((0,-1,0),[(0,0,0),(1,0,0),(1,0,1),(0,0,1)]),
           ((0,1,0),[(0,1,0),(0,1,1),(1,1,1),(1,1,0)]),
           ((0,0,-1),[(0,0,0),(0,1,0),(1,1,0),(1,0,0)]),
           ((0,0,1),[(0,0,1),(1,0,1),(1,1,1),(0,1,1)])]
    # Convert the lattice once. Every face belongs to one cube; omit internal
    # faces inside a solid rigid stone. Fracture interfaces stay closed.
    for key,(_,token) in sorted(cells.items()):
        cx,cy,cz=blender_center(key,step); bone=assignments[key]
        color=linear('#91958b' if grey else spec['palette_srgb'][token])
        for direction,quad in faces:
            # Directions here are Blender X/Y/Z; canonical lattice is X/Yup/Z.
            dx,dby,dbz=direction; neighbor=(key[0]+dx,key[1]+dbz,key[2]-dby)
            if neighbor in cells and assignments[neighbor]==bone: continue
            start=len(vertices)
            vertices.extend((cx+(qx-.5)*step,cy+(qy-.5)*step,cz+(qz-.5)*step) for qx,qy,qz in quad)
            polygons.append(tuple(range(start,start+4)))
            colors.extend([color]*4)
            groups.setdefault(bone,[]).extend(range(start,start+4))
            slots.append(0 if grey else (1 if token=='B' else 2 if token=='G' else 0))
    mesh=bpy.data.meshes.new('Cairn_VoxelSurface'); mesh.from_pydata(vertices,[],polygons); mesh.update()
    obj=bpy.data.objects.new('Body',mesh); bpy.context.collection.objects.link(obj)
    for mat in (material('Stone_cloth'),material('Brass',.35),material('Amber',0,.35)):
        mesh.materials.append(mat)
    attr=mesh.color_attributes.new(name='VoxelColor',type='FLOAT_COLOR',domain='CORNER')
    for loop,col in zip(attr.data,colors): loop.color=col
    for poly,slot in zip(mesh.polygons,slots): poly.material_index=slot; poly.use_smooth=False
    if armature:
        obj.parent=armature
        mod=obj.modifiers.new('RigidVoxelSkin','ARMATURE'); mod.object=armature
        for bone,indices in groups.items(): obj.vertex_groups.new(name=bone).add(indices,1,'REPLACE')
    return obj


def look_at(camera,target):
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()


def setup_scene():
    scene=bpy.context.scene
    reproducible_renderer(scene)
    scene.render.resolution_percentage=100; scene.render.image_settings.file_format='PNG'
    scene.render.fps=30; scene.render.fps_base=1; scene.render.dither_intensity=0
    scene.render.film_transparent=False; scene.view_settings.view_transform='Standard'
    scene.view_settings.look='None'; scene.view_settings.exposure=0; scene.view_settings.gamma=1
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.75,.75,.75,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6
    # A white reference background is compositor-only, lighting stays fixed.
    scene.render.film_transparent=False
    nodes=scene.world.node_tree.nodes; links=scene.world.node_tree.links
    background=nodes['Background']; background.inputs['Strength'].default_value=.6
    camera_bg=nodes.new('ShaderNodeBackground'); camera_bg.inputs['Color'].default_value=(1,1,1,1)
    camera_bg.inputs['Strength'].default_value=1
    light_path=nodes.new('ShaderNodeLightPath'); mix=nodes.new('ShaderNodeMixShader')
    links.new(light_path.outputs['Is Camera Ray'],mix.inputs[0])
    links.new(background.outputs[0],mix.inputs[1]); links.new(camera_bg.outputs[0],mix.inputs[2])
    links.new(mix.outputs[0],nodes['World Output'].inputs[0])
    for name,energy,rot in [('Key',2.2,(35,-25,140)),('Fill',.8,(40,20,20))]:
        data=bpy.data.lights.new(name,'SUN'); data.energy=energy; data.use_shadow=False
        obj=bpy.data.objects.new(name,data); bpy.context.collection.objects.link(obj)
        obj.rotation_euler=tuple(math.radians(x) for x in rot)
    data=bpy.data.cameras.new('ReviewCamera'); data.type='ORTHO'; data.ortho_scale=3.9
    camera=bpy.data.objects.new('ReviewCamera',data); bpy.context.collection.objects.link(camera); scene.camera=camera
    return camera


def render(path,camera,view='iso',resolution=(640,640),scale=3.9,ground=False):
    scene=bpy.context.scene; target=(0,0,1.6)
    # Frozen authoring files may retain a previous renderer configuration.
    reproducible_renderer(scene)
    positions={'front':(0,9,1.6),'back':(0,-9,1.6),'side':(9,0,1.6),
               'left':(-9,0,1.6),'top':(0,.0001,10),'iso':(7,9,7.2)}
    camera.location=positions[view]; look_at(camera,target); camera.data.ortho_scale=scale
    scene.render.resolution_x,scene.render.resolution_y=resolution
    scene.render.filepath=str(Path(path).resolve()); Path(path).parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.render.render(write_still=True)
    remove_render_metadata(Path(path))
