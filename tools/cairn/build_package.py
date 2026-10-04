"""Build frozen Cairn sources with a shared ten-minute process deadline."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
ASSET=Path('assets/characters/bosses/cairn')
BLENDER=r'D:\ProgramFiles\cube-siege-art-tools\blender-5.2.1-windows-x64\blender.exe'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender',default=os.environ.get('BLENDER_BIN',BLENDER))
    args=parser.parse_args()
    deadline=time.monotonic()+600
    logs=ROOT/'.local/cairn_build_logs'; logs.mkdir(parents=True,exist_ok=True)
    def run(name,command):
        remaining=deadline-time.monotonic()
        if remaining<=0: raise TimeoutError('Cairn build exceeded ten minutes')
        print('STAGE',name,flush=True)
        with (logs/(name+'.log')).open('w',encoding='utf-8') as log:
            result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
                                  timeout=remaining,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        if result.returncode: raise RuntimeError(f'{name} failed; see {logs/(name+".log")}')
    blender=[args.blender,'--background','--factory-startup','--python-exit-code','1','--python']
    # This branch only renders frozen layer alternatives; it never authors source.
    run('blockouts',blender+['tools/cairn/author_blend.py','--','--blockouts'])
    run('blender',blender+['tools/cairn/build_cairn.py'])
    run('glb_validation',[sys.executable,'tools/cairn/verify_glb_motion.py','--asset',str(ASSET),
                           '--output',str(ASSET/'review/glb_validation.json')])
    run('media',[sys.executable,'tools/cairn/compose_review.py','--review-dir',str(ASSET/'review'),
                 '--reference',str(ASSET/'references/selected_cairn.png'),'--source-fps','30','--fps','30',
                 '--timeout-seconds',str(min(180,deadline-time.monotonic()-5))])
    run('death_validation',[sys.executable,'tools/cairn/validate_death_source.py'])
    run('godot',[sys.executable,'tools/cairn/run_godot_probe.py','--render','--movie',
                 '--timeout',str(min(300,deadline-time.monotonic()-5))])
    run('engine_validation',[sys.executable,'tools/cairn/validate_engine_poses.py'])
    print(f'CAIRN_BUILD_COMPLETE seconds={600-(deadline-time.monotonic()):.2f}',flush=True)

if __name__=='__main__': main()
