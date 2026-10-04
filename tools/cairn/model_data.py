"""Cairn's lattice decoding and solid cubic fracture regions (no Blender dependency)."""
from __future__ import annotations
from collections import defaultdict


def decode(spec):
    cells={}
    for part,data in spec['parts'].items():
        ox,oy,oz=data['origin_grid']
        for iy,rows in enumerate(data['layers_y']):
            for iz,row in enumerate(rows):
                for ix,token in enumerate(row):
                    if token=='.': continue
                    key=(ox+ix,oy+iy,oz+iz)
                    if key in cells: raise ValueError(f'Overlapping voxel cell {key}')
                    if token not in spec['palette_srgb']: raise ValueError(f'Unknown token {token}')
                    cells[key]=(part,token)
    return cells


def blender_center(key, step):
    x,y,z=key
    return ((x+.5)*step,-(z+.5)*step,(y+.5)*step)


def fragments_for(cells,step):
    fragments=[]; assignments={}
    for part in sorted({v[0] for v in cells.values()}):
        remaining={k for k,v in cells.items() if v[0]==part}
        # Consume large complete cubes first, then exposed one-cell steps.
        for size in (5,4,3,2,1):
            for base in sorted(tuple(remaining),key=lambda k:(k[1],k[2],k[0])):
                if base not in remaining: continue
                x,y,z=base
                region={(x+dx,y+dy,z+dz) for dx in range(size)
                        for dy in range(size) for dz in range(size)}
                if not region.issubset(remaining): continue
                remaining.difference_update(region)
                ident=f'rubble_{len(fragments):04d}'
                center=((x+size*.5)*step,-(z+size*.5)*step,(y+size*.5)*step)
                fragments.append({'id':ident,'center':center,'size':size*step,'parent':part,'cells':sorted(region)})
                for key in region: assignments[key]=ident
        if remaining: raise AssertionError('Fragment packing omitted cells')
    return fragments,assignments
