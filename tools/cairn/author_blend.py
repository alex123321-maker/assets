"""Author Cairn's editable armature/actions from its frozen voxel layers."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from model_data import decode,fragments_for,blender_center
from blender_scene import create_mesh,setup_scene,render
from leg_kinematics import solve_leg

ROOT=HERE.parents[1]; ASSET=ROOT/'assets/characters/bosses/cairn'


def clear():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for action in list(bpy.data.actions): bpy.data.actions.remove(action)


def make_rig(fragments):
    definitions={
        'root':((0,0,0),None), 'pelvis':((0,0,1.55),'root'),
        'spine':((0,0,1.65),'root'), 'head':((0,0,2.35),'spine'),
    }
    for side,sign in [('L',1),('R',-1)]:
        definitions.update({
            'upper_arm.'+side:((sign*.7,0,2.2),'spine'),
            'forearm.'+side:((sign*1.0,0,1.65),'upper_arm.'+side),
            'hand.'+side:((sign*1.0,0,1.1),'forearm.'+side),
            'thigh.'+side:((sign*.5,-.31,1.4),'root'),
            'shin.'+side:((sign*.55,-.31,.9),'thigh.'+side),
            'foot.'+side:((sign*.55,-.31,.3),'shin.'+side),
        })
    for fragment in fragments: definitions[fragment['id']]=(fragment['center'],fragment['parent'])
    data=bpy.data.armatures.new('CairnSkeleton'); arm=bpy.data.objects.new('Cairn',data)
    bpy.context.collection.objects.link(arm); bpy.context.view_layer.objects.active=arm
    arm.select_set(True); bpy.ops.object.mode_set(mode='EDIT')
    for name,(head,parent) in definitions.items():
        bone=data.edit_bones.new(name); bone.head=head; bone.tail=Vector(head)+Vector((0,.1,0)); bone.roll=0
    for name,(_,parent) in definitions.items():
        if parent: data.edit_bones[name].parent=data.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT'); arm.show_in_front=True
    for pb in arm.pose.bones: pb.rotation_mode='XYZ'
    return arm,definitions


def reset(arm):
    for bone in arm.pose.bones:
        bone.location=(0,0,0); bone.rotation_euler=(0,0,0); bone.scale=(1,1,1)


def leg_pose(arm,side,y,lift,root_z):
    pose=solve_leg(y,lift,root_z,side=side)
    if not pose['reachable']: raise ValueError('Unreachable authored foot target')
    arm.pose.bones['thigh.'+side].rotation_euler.x=pose['thigh_x']
    arm.pose.bones['shin.'+side].rotation_euler.x=pose['shin_x']
    arm.pose.bones['foot.'+side].rotation_euler.x=pose['foot_x']


def body_pose(arm,clip,t):
    reset(arm)
    root_z=-.045
    if clip=='idle':
        root_z=-.045+.003*math.sin(t*math.tau)
        arm.pose.bones['spine'].rotation_euler.x=math.radians(.6)*math.sin(t*math.tau)
        arm.pose.bones['head'].rotation_euler.z=math.radians(1.2)*math.sin(t*math.tau)
        for side in ('L','R'): leg_pose(arm,side,0,0,root_z)
    elif clip=='move':
        root_z=-.06+.012*math.cos(t*math.tau*2)
        for side,phase in [('L',t),('R',(t+.5)%1)]:
            phase%=1
            if phase<.5: y=.2875-1.15*phase; lift=0
            else:
                p=(phase-.5)*2; y=-.2875+.575*p; lift=.16*math.sin(math.pi*p)
            leg_pose(arm,side,y,lift,root_z)
            arm.pose.bones['upper_arm.'+side].rotation_euler.x=math.radians(9)*math.sin(phase*math.tau)
        arm.pose.bones['spine'].rotation_euler.x=math.radians(2.5)
    elif clip=='attack_0':
        # Both heavy fists load, release a chest-centred pulse, then recover.
        if t<=.65:
            p=t/.65; rise=.5-.5*math.cos(p*math.pi)
            angle=100*rise; root_z=-.045-.07*rise
        elif t<=.8:
            p=(t-.65)/.15; angle=100-75*p; root_z=-.115-.025*math.sin(math.pi*p)
        else:
            p=(t-.8)/.2; angle=25*(1-p); root_z=-.115+.07*p
        for side in ('L','R'):
            arm.pose.bones['upper_arm.'+side].rotation_euler.x=math.radians(angle)
            leg_pose(arm,side,0,0,root_z)
        arm.pose.bones['spine'].rotation_euler.x=math.radians(2)
    elif clip=='attack_1':
        # Release is at WARNING entry; the later warning is projectile flight.
        root_z=-.07
        if t<.14: angle=112-65*(t/.14)
        elif t<.65: angle=47-22*((t-.14)/.51)
        elif t<.8: angle=25
        else: angle=25*(1-(t-.8)/.2)
        arm.pose.bones['upper_arm.R'].rotation_euler.x=math.radians(angle)
        arm.pose.bones['upper_arm.L'].rotation_euler.x=math.radians(15 if t<.8 else 15*(1-t)/.2)
        arm.pose.bones['head'].rotation_euler.z=math.radians(-3)
        for side in ('L','R'): leg_pose(arm,side,0,0,root_z)
    arm.pose.bones['root'].location.z=root_z


def set_linear(action):
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points: key.interpolation='LINEAR'


def author_actions(arm,definitions,death_motion):
    arm.animation_data_create(); actions=[]
    durations={'idle':60,'move':15,'attack_0':30,'attack_1':30}
    for clip,frames in durations.items():
        action=bpy.data.actions.new(clip); arm.animation_data.action=action
        for frame in range(frames+1):
            body_pose(arm,clip,frame/frames)
            for name in definitions:
                if name.startswith('rubble_'): continue
                bone=arm.pose.bones[name]
                bone.keyframe_insert('location',frame=frame,group=name)
                bone.keyframe_insert('rotation_euler',frame=frame,group=name)
        for name in definitions:
            if name.startswith('rubble_'):
                bone=arm.pose.bones[name]
                for frame in (0,frames): bone.keyframe_insert('location',frame=frame,group=name)
        set_linear(action); actions.append(action)
        action['duration_seconds']=frames/30; action['loop']=clip in ('idle','move')
    reset(arm)
    action=bpy.data.actions.new('death'); arm.animation_data.action=action
    for name in definitions:
        pb=arm.pose.bones[name]
        pb.keyframe_insert('location',frame=0,group=name); pb.keyframe_insert('rotation_euler',frame=0,group=name)
    # A short still beat makes the ensuing loss of structure easy to read.
    ids=death_motion['ids']; origins={name:Vector(center) for name,center in zip(ids,death_motion['frames'][0]['centers'])}
    bag=action.layers[0].strips[0].channelbags[0]
    for index,name in enumerate(ids):
        path=arm.pose.bones[name].path_from_id('location')
        for axis in range(3):
            curve=bag.fcurves.find(path,index=axis)
            curve.keyframe_points.add(len(death_motion['frames']))
            coordinates=[0,0]
            for sample in death_motion['frames']:
                coordinates.extend([7.5+sample['time']*30,sample['centers'][index][axis]-origins[name][axis]])
            # Sorted LINEAR keys already define the curve. update() silently
            # merges nearby fractional collision keys (<0.01 frame).
            curve.keyframe_points.foreach_set('co',coordinates)
    set_linear(action); actions.append(action)
    action['duration_seconds']=.25+death_motion['frames'][-1]['time']; action['loop']=False
    reset(arm); arm.animation_data.action=None
    for action in actions:
        track=arm.animation_data.nla_tracks.new(); track.name=action.name
        track.strips.new(action.name,0,action); track.mute=True
    return actions


def blockouts():
    review=ASSET/'review'; review.mkdir(exist_ok=True)
    receipt={'version':1}
    for variant,filename in [('a','voxels.json'),('b','blockout_b.json')]:
        clear(); spec=json.loads((ASSET/'source'/filename).read_text()); cells=decode(spec)
        assignments={k:v[0] for k,v in cells.items()}
        create_mesh(spec,cells,assignments,grey=True); camera=setup_scene()
        render(review/f'blockout_{variant}_iso.png',camera)
        scene=bpy.context.scene; image=review/f'blockout_{variant}_iso.png'; source=ASSET/'source'/filename
        receipt['before' if variant=='a' else 'after']={
            'source':source.relative_to(ROOT).as_posix(),
            'source_sha256':hashlib.sha256(source.read_bytes().replace(b'\r\n',b'\n')).hexdigest(),
            'image':image.relative_to(ROOT).as_posix(),'image_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),
            'settings':{'camera_matrix':[list(row) for row in camera.matrix_world],
                'ortho_scale':camera.data.ortho_scale,
                'lights':[{'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),
                           'matrix':[list(row) for row in o.matrix_world]} for o in sorted(scene.objects,key=lambda o:o.name) if o.type=='LIGHT'],
                'world_color':{'ambient_linear_rgba':list(scene.world.node_tree.nodes['Background'].inputs['Color'].default_value),
                               'ambient_strength':scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value},
                'resolution':[scene.render.resolution_x,scene.render.resolution_y],
                'color_management':{key:getattr(scene.view_settings,key) for key in ('view_transform','look','exposure','gamma')},
                'engine':scene.render.engine,'blender_version':bpy.app.version_string}}
        render(review/f'blockout_{variant}_front.png',camera,view='front')
    (review/'blockout_comparison_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')


def main():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser(); parser.add_argument('--blockouts',action='store_true')
    options=parser.parse_args(args)
    if options.blockouts: blockouts(); return
    clear(); spec_path=ASSET/'source/voxels.json'; spec=json.loads(spec_path.read_text())
    cells=decode(spec); fragments,assignments=fragments_for(cells,spec['voxel_size_m'])
    motion=json.loads((ASSET/'source/death_motion.json').read_text())
    if motion['input_sha256']!=hashlib.sha256(spec_path.read_bytes().replace(b'\r\n',b'\n')).hexdigest():
        raise ValueError('Death motion belongs to older voxel source; re-author it')
    arm,definitions=make_rig(fragments); body=create_mesh(spec,cells,assignments,arm)
    actions=author_actions(arm,definitions,motion); camera=setup_scene()
    bpy.context.scene.frame_set(0); bpy.context.scene.frame_end=90
    descriptors=[{'id':f'{k[0]}:{k[1]}:{k[2]}','center':blender_center(k,spec['voxel_size_m']),
                  'size':spec['voxel_size_m'],'bone':assignments[k]} for k in sorted(cells)]
    (ASSET/'source/rig_contract.json').write_text(json.dumps({
        'cubes':descriptors,'fragments':[{k:v for k,v in f.items() if k!='cells'} for f in fragments],
        'animation_phase_map':{'warning':[0,.65],'active':[.65,.8],'recovery':[.8,1]},
        'clips':{a.name:{'duration_seconds':a['duration_seconds'],'loop':a['loop']} for a in actions},
        'rest_coordinates':'Blender Z-up, +Y forward; glTF Y-up, -Z forward',
        'articulated_bones':len(definitions)-len(fragments)},indent=2)+'\n',encoding='utf-8')
    arm['voxel_source_sha256']=hashlib.sha256(spec_path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
    bpy.ops.wm.save_as_mainfile(filepath=str(ASSET/'source/model.blend'),compress=True)
    print(json.dumps({'source_saved':str(ASSET/'source/model.blend'),'cubes':len(cells),'fragments':len(fragments),'bones':len(definitions)}))


if __name__=='__main__': main()
