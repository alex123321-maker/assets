"""Read frozen .blend; export, validate cube volumes, and render real rig evidence."""
from __future__ import annotations
import argparse
import json
import hashlib
import math
import sys
from pathlib import Path
import bpy

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
from blender_scene import render
from validate_voxel_motion import validate_asset
from model_data import decode,fragments_for,blender_center


def reset(arm):
    for bone in arm.pose.bones:
        bone.location=(0,0,0); bone.rotation_euler=(0,0,0); bone.scale=(1,1,1)


def pose_frame(arm,frame,label):
    scene=bpy.context.scene; scene.frame_set(int(math.floor(frame)),subframe=frame%1)
    return {'frame':label,'bone_matrices':{bone.name:[list(row) for row in
        (arm.matrix_world @ bone.matrix @ bone.bone.matrix_local.inverted())]
        for bone in arm.pose.bones if bone.name.startswith('rubble_')}}


def main():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser(); parser.add_argument('--asset',default='assets/characters/bosses/cairn')
    parser.add_argument('--quick',action='store_true'); parser.add_argument('--validate-only',action='store_true'); options=parser.parse_args(args)
    asset=ROOT/options.asset; review=asset/'review'; review.mkdir(exist_ok=True)
    output=asset/'output'; output.mkdir(exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(asset/'source/model.blend'))
    arm=bpy.data.objects['Cairn']; body=bpy.data.objects['Body']; camera=bpy.data.objects['ReviewCamera']
    contract=json.loads((asset/'source/rig_contract.json').read_text())
    source_bytes=(asset/'source/voxels.json').read_bytes()
    source_hash=hashlib.sha256(source_bytes.replace(b'\r\n',b'\n')).hexdigest()
    motion=json.loads((asset/'source/death_motion.json').read_text())
    if arm.get('voxel_source_sha256')!=source_hash or motion['input_sha256']!=source_hash:
        raise ValueError('Frozen rig/death does not match current voxel source; author before build')
    spec=json.loads(source_bytes); cells=decode(spec)
    fragments,assignments=fragments_for(cells,spec['voxel_size_m'])
    expected=[{'id':f'{k[0]}:{k[1]}:{k[2]}','center':list(blender_center(k,spec['voxel_size_m'])),
               'size':spec['voxel_size_m'],'bone':assignments[k]} for k in sorted(cells)]
    if contract['cubes']!=expected or len(contract['fragments'])!=len(fragments):
        raise ValueError('Frozen rig contract differs from current source cube/fragment assignments')
    actions={name:bpy.data.actions[name] for name in contract['clips']}
    reset(arm); arm.animation_data.action=None
    for track in arm.animation_data.nla_tracks: track.mute=True
    bpy.context.scene.frame_set(0)
    if not options.validate_only:
        for view in ['iso','front','back','side','left','top']:
            render(review/f'{view}.png',camera,view,resolution=(800,800))
    # Real posed cubic volumes, sampled at60Hz and animation boundaries.
    samples=[]; clip_reports={}
    for clip,action in actions.items():
        arm.animation_data.action=action; end=contract['clips'][clip]['duration_seconds']*30
        frames=sorted(set([0,end*.25,end*.5,end*.75,end])) if options.quick else [i*.5 for i in range(int(end*2)+1)]
        if clip=='death':
            # CCD linear-event validation lives in the authored physics source.
            # Every regular60Hz pose is checked here after actual skinning.
            frames=sorted(set(frames+[7.5,end]))
        clip_samples=[pose_frame(arm,frame,f'{clip}:{frame:.3f}') for frame in frames]
        samples.extend(clip_samples)
        clip_reports[clip]=validate_asset(contract['cubes'],clip_samples,tolerance=1e-5,max_issues=40)
    report={'pass':all(r['pass'] for r in clip_reports.values()),'cube_count':len(contract['cubes']),
            'frames_checked':len(samples),'rest_overlap_count':max(r['rest_overlap_count'] for r in clip_reports.values()),
            'animated_overlap_count':sum(r['animated_overlap_count'] for r in clip_reports.values()),
            'clips':clip_reports,'issues':[i for r in clip_reports.values() for i in r['issues']]}
    (review/'cube_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('CUBE_VALIDATION',json.dumps({k:v for k,v in report.items() if k!='issues'}))
    if not report['pass']:
        print(json.dumps(report['issues'][:15],indent=2)); raise ValueError('Cube penetration in authored animation')
    if options.validate_only: return
    reset(arm); arm.animation_data.action=None; bpy.context.scene.frame_set(0)
    bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); body.select_set(True)
    bpy.context.view_layer.objects.active=arm
    from io_scene_gltf2.blender.exp.animation.fcurves import channels as gltf_channels
    original_groups=gltf_channels.get_channel_groups
    def stable_groups(*args,**kwargs):
        targets,sampled,extra=original_groups(*args,**kwargs)
        # Blender 5.2 deduplicates sampled channels with a set. Its tuples are
        # (object_uuid, type, property, bone_name); the export tree creates a
        # random UUID each run. Groups belong to one object, so exclude that
        # UUID and sort the remaining stable fields without changing any keys.
        sampled.sort(key=lambda channel:tuple('' if value is None else str(value)
                                             for value in channel[1:]))
        return targets,sampled,extra
    gltf_channels.get_channel_groups=stable_groups
    try:
        bpy.ops.export_scene.gltf(filepath=str(output/'model.glb'),export_format='GLB',use_selection=True,
            export_yup=True,export_materials='EXPORT',export_animations=True,export_skins=True,
            export_all_influences=False,export_animation_mode='ACTIONS',export_force_sampling=False,
            export_def_bones=True,export_extras=True)
    finally:
        gltf_channels.get_channel_groups=original_groups
    for track in arm.animation_data.nla_tracks: track.mute=True
    # Render consecutive real-rig frames. Fast quick runs retain key phases only.
    for clip,action in actions.items():
        arm.animation_data.action=action; end=round(contract['clips'][clip]['duration_seconds']*30)
        frames=range(end+1) if not options.quick else sorted(set([0,end//4,end//2,3*end//4,end]))
        scale=6.8 if clip=='death' else 4.8 if clip.startswith('attack') else 4.0
        clip_dir=review/'frames'/clip
        if clip_dir.exists():
            for old in clip_dir.glob('frame_????.png'): old.unlink()
        for frame in frames:
            bpy.context.scene.frame_set(frame)
            render(review/'frames'/clip/f'frame_{frame:04d}.png',camera,'iso',resolution=(480,480),scale=scale)
    reset(arm); arm.animation_data.action=None; bpy.context.scene.frame_set(0)
    metrics={
        'asset':'cairn','triangles':sum(len(p.vertices)-2 for p in body.data.polygons),
        'materials':len(body.data.materials),'bones':len(arm.data.bones),
        'articulated_bones':contract['articulated_bones'],'fracture_cube_bones':len(contract['fragments']),
        'source_voxels':len(contract['cubes']),'voxel_size_m':contract['cubes'][0]['size'],
        'dimensions':{'x':round(body.dimensions.x,6),'y':round(body.dimensions.y,6),'z':round(body.dimensions.z,6)},
        'animation_details':contract['clips'],'pivot':'bottom-center','forward':'glTF -Z',
        'blender_version':bpy.app.version_string,'render_engine':bpy.context.scene.render.engine,
        'glb_size_bytes':(output/'model.glb').stat().st_size,'motion_samples_checked':len(samples),
        'cube_validation_tolerance_m':1e-5,
        'limits':'Blender rig sample validation is finite; continuous death segments checked separately. Engine demonstration is standalone.'}
    (review/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf-8')
    print('BUILD_METRICS',json.dumps(metrics))


if __name__=='__main__': main()
