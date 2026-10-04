"""Author the Cairn source on a unique Y-up voxel lattice; never a build step."""
from __future__ import annotations

import hashlib
import json
import math
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSET = ROOT / 'assets/characters/bosses/cairn'
STEP = 0.1
PALETTE = {
    'S': '#777d70', 'L': '#92988a', 'D': '#50584e',
    'M': '#4b5d32', 'N': '#637747', 'I': '#ded0aa',
    'K': '#171d17', 'B': '#d0aa5e', 'G': '#ffb432',
    'C': '#493c31', 'T': '#62503e',
}


def author(variant='a'):
    cells = {}

    def block(part, x0, x1, y0, y1, z0, z1, token='S', overwrite=False):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    key = (x, y, z)
                    if key in cells and cells[key][0] != part:
                        raise ValueError(f'Articulation overlap {key}: {part}/{cells[key]}')
                    if key not in cells or overwrite:
                        cells[key] = (part, token)

    # Body solids and surface pigments share cells: insets never overlay cubes.
    block('pelvis', -5, 4, 14, 15, -2, 2, 'C')
    block('pelvis', -2, 1, 10, 13, -3, -3, 'T')
    block('pelvis', -1, 0, 9, 13, -3, -3, 'C', True)
    block('spine', -5, 4, 17, 22, -2, 2)
    block('spine', -5, 4, 17, 22, -3, -3, 'L')
    block('spine', -4, 3, 17, 22, 3, 3)
    def seal(x0, x1, y0, y1, frame_z):
        # The base, outer ring and protruding centre occupy different complete
        # lattice cells. Replacing a token never overlays another solid.
        block('spine', x0, x1, y0, y1, -4, -4, 'B')
        block('spine', x0+1, x1-1, y0+1, y1-1, -4, -4, 'C', True)
        block('spine', x0, x0, y0, y1, frame_z, frame_z, 'B')
        block('spine', x1, x1, y0, y1, frame_z, frame_z, 'B')
        block('spine', x0+1, x1-1, y0, y0, frame_z, frame_z, 'B')
        block('spine', x0+1, x1-1, y1, y1, frame_z, frame_z, 'B')
        block('spine', x0+1, x1-1, y0+1, y1-1, frame_z-1, -5, 'G')
    seal(-2, 1, 17, 20, -5)
    seal(-5, -3, 20, 22, -4)
    seal(2, 4, 20, 22, -4)
    # Small dark cubic connectors occupy sockets carved in the larger solids.
    # Recessed cheeks, continuous ivory brow and square amber pupils.
    block('head', -3, 2, 24, 28, -2, 2)
    block('head', -3, 2, 24, 26, -3, -3, 'I')
    block('head', -3, 2, 25, 25, -3, -3, 'K', True)
    block('head', -2, -2, 25, 25, -3, -3, 'G', True)
    block('head', 1, 1, 25, 25, -3, -3, 'G', True)
    block('head', -3, 2, 26, 26, -4, -4, 'I')
    block('head', -3, 2, 24, 24, -4, -4, 'I')
    block('head', -4, -4, 24, 27, -1, 1, 'D')
    block('head', 3, 3, 24, 27, -1, 1, 'D')
    block('head', -2, 1, 29, 30, -2, 2)
    block('head', -1, 0, 31, 31, -2, 2, 'L')
    block('head', -1, 0, 23, 23, 0, 1, 'D')
    # Waist socket avoids the visible disconnected blockout silhouette.
    for key in list(cells):
        x,y,z=key
        if cells[key][0]=='spine' and y==17 and -2<=z<=2:
            del cells[key]
    block('pelvis', -3, 2, 16, 16, -1, 1, 'D')
    # Separate narrow articulation cores and coarse shoulder/fist plates.
    for side, sign in [('L', 1), ('R', -1)]:
        def limb(part, a, b, ya, yb, za, zb, token='S', overwrite=False):
            xa, xb = (a, b) if sign == 1 else (-b - 1, -a - 1)
            block(part + '.' + side, xa, xb, ya, yb, za, zb, token, overwrite)
        limb('thigh', 3, 6, 10, 12, -1, 2, 'D')
        limb('thigh', 3, 6, 11, 12, -2, -2, 'S')
        limb('shin', 4, 7, 4, 5, -1, 2, 'D')
        limb('shin', 3, 7, 6, 8, -2, 2, 'S')
        limb('shin', 3, 7, 8, 8, -3, -3, 'L')
        limb('foot', 3, 8, 0, 1, -4, 2, 'S')
        limb('foot', 4, 7, 2, 2, -3, 2, 'L')
        limb('upper_arm', 7, 9, 17, 20, -1, 1, 'D')
        # Tiered, square-edged shoulder slabs, no bevel modifier.
        limb('upper_arm', 6, 10, 21, 24, -2, 2, 'S')
        limb('upper_arm', 7, 9, 25, 25, -1, 1, 'L')
        limb('upper_arm', 6, 11, 20, 20, -3, 3, 'L')
        limb('upper_arm', 11, 11, 21, 22, -2, 2, 'S')
        limb('upper_arm', 6, 10, 21, 24, -3, -3, 'S')
        limb('upper_arm', 6, 10, 21, 24, 3, 3, 'S')
        limb('forearm', 8, 11, 11, 15, -2, 2, 'S')
        limb('forearm', 7, 11, 15, 15, -3, 3, 'L')
        limb('forearm', 8, 12, 11, 14, -3, -3, 'L')
        limb('forearm', 12, 12, 11, 13, -2, 1, 'S')
        limb('hand', 8, 11, 9, 10, -2, 2, 'D')
        limb('hand', 9, 11, 9, 10, -3, -3, 'S')
        limb('thigh', 4, 5, 13, 13, 0, 1, 'D')
        limb('shin', 5, 6, 3, 3, 0, 1, 'D')
        limb('upper_arm', 7, 8, 16, 16, 0, 1, 'D')
        limb('thigh', 4, 5, 9, 9, 2, 2, 'D')
    # A stepped fist tip replaces the straight rectangular lower box. Trim
    # existing outer corners only; articulation cores and inner clearance stay.
    for key, (part, token) in list(cells.items()):
        x,y,z = key
        lateral = abs(x+.5)
        if part.startswith('forearm.') and y==11 and lateral>=11.5 and (z<=-1 or z>=1):
            del cells[key]
        elif part.startswith('hand.') and y==9 and (lateral<=8.5 or lateral>=11.5) and (z<=-2 or z>=2):
            del cells[key]
        elif part.startswith('hand.') and y==10 and lateral<=8.5 and z==-2:
            cells[key]=(part,'L')
    # Thin sockets around hip and ankle connector cubes leave swept clearance.
    for key in list(cells):
        x,y,z=key; part=cells[key][0]
        lateral=abs(x+.5)
        if part=='pelvis' and y in (14,15) and lateral>=3.5:
            del cells[key]
        elif part.startswith('foot.') and y==2 and 4.5<=lateral<=7.5 and -1<=z<=1:
            del cells[key]
        elif part.startswith('shin.') and (y==3 or (y in (4,5) and z!=2) or (y==6 and z<0)):
            del cells[key]
    # Rear ankle posts face-connect to the boot while remaining outside the
    # swept calf. A third post cell at Y4 was rejected by actual stride SAT.
    block('foot.L',5,5,2,3,3,3,'D')
    block('foot.R',-6,-6,2,3,3,3,'D')
    # Match the reference's width/height ratio: arms move one lattice column
    # inward; the one-cell outer fingertip plate is removed, never scaled.
    adjusted={}
    for (x,y,z),(part,token) in cells.items():
        if part.startswith(('upper_arm.','forearm.','hand.')):
            if part.startswith('forearm.') and abs(x+.5)>12:
                continue
            if part.startswith('upper_arm.'):
                x += -1 if x>=0 else 1
        key=(x,y,z)
        if key in adjusted: raise ValueError(f'Duplicate shifted arm cell {key}')
        adjusted[key]=(part,token)
    cells=adjusted
    # Broad, deterministic stone/mineral patches, with coherent variation.
    fixed = list(cells.items())
    for (x,y,z),(part,token) in fixed:
        if token not in {'S','L'}:
            continue
        # Low-frequency fields give connected mineral seams with uneven
        # stepped boundaries, rather than a repeated rectangular checker.
        edge = ((x*17 + y*11 + z*23) % 13 - 6) / 70
        moss_field = (math.sin(.39*x + .23*z) + .75*math.cos(.31*y - .19*x)
                      + .4*math.sin(.63*z + .22*y) + edge)
        stone_field = math.sin(.46*x + .28*y) + .6*math.cos(.38*z - .17*y) + edge
        moss = moss_field > 1.28
        if moss and (part != 'head' or y >= 27):
            cells[x,y,z] = (part, 'M' if moss_field > 1.55 else 'N')
        elif stone_field > .95:
            cells[x,y,z] = (part,'L')
        elif stone_field < -.95:
            cells[x,y,z] = (part,'S')
    # Frontal shoulder rims and knuckle steps use whole-cell pigment/infill.
    for key,(part,token) in list(cells.items()):
        x,y,z=key; a=int(abs(x+.5))
        if part.startswith('upper_arm.') and z==-3:
            if a==5 or (a==9 and y<=22): cells[key]=(part,'L')
            elif (a,y) in {(6,22),(7,22),(6,23),(7,24)}: cells[key]=(part,'M')
            elif (a,y) in {(7,23),(8,24)}: cells[key]=(part,'N')
        elif part.startswith('forearm.') and z==-3:
            if (a,y) in {(8,13),(9,13),(9,12)}: cells[key]=(part,'M')
            elif (a,y)==(8,14): cells[key]=(part,'N')
            elif a>=9 and y<=12: cells[key]=(part,'S')
    # Gray bottom borders separate the three seals in frontal projection.
    # These are pigment replacements on existing cells, not new geometry.
    for x in (-5,-4,-3,2,3,4): cells[x,20,-4]=('spine','L')
    if variant == 'b':
        # A restrained alternative upper-body mass for silhouette selection.
        for key in list(cells):
            part,_=cells[key]
            x,y,z=key
            if 'upper_arm' in part and y>=24 and abs(x)>=9:
                del cells[key]
    parts = {}
    for part in sorted({v[0] for v in cells.values()}):
        mine = {k:v[1] for k,v in cells.items() if v[0]==part}
        lo = [min(k[a] for k in mine) for a in range(3)]
        hi = [max(k[a] for k in mine) for a in range(3)]
        layers = []
        for y in range(lo[1],hi[1]+1):
            rows = [''.join(mine.get((x,y,z),'.') for x in range(lo[0],hi[0]+1))
                    for z in range(lo[2],hi[2]+1)]
            layers.append(rows)
        parts[part]={'origin_grid':lo,'layers_y':layers}
    return {'schema_version':1,'asset':'cairn','coordinate_system':'X right, Y up, Z forward negative',
            'voxel_size_m':STEP,'palette_srgb':PALETTE,'variant':variant,'parts':parts,
            'notes':'One occupied lattice cell is one rigid cube. Surface colours replace tokens; they never add overlapping layers.'}


def main():
    source=ASSET/'source'; source.mkdir(parents=True,exist_ok=True)
    reference=ASSET/'references/selected_cairn.png'
    if not reference.exists():
        shutil.copyfile(ASSET/'references/catalog_2026-10-04/cairn_five_views.png',reference)
    (ASSET/'references/selected_cairn_provenance.json').write_text(json.dumps({
        'status':'candidate','source_page':'https://chatgpt.com/space/page_ac6de68b0c28819193cb8bb93156c5bb',
        'source_local':'references/catalog_2026-10-04/cairn_five_views.png',
        'sha256':hashlib.sha256(reference.read_bytes()).hexdigest(),
        'selection':'User request to select and reproduce one boss; cairn announced and retained after voxel clarification.',
        'original_tool':'image_gen.imagegen','reference_snapshot_only':True},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for variant in ('a','b'):
        filename='voxels.json' if variant=='a' else 'blockout_b.json'
        (source/filename).write_text(json.dumps(author(variant),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    manifest={'name':'cairn','type':'voxel_rigged','version':1,'source':'source/model.blend',
              'outputs':{'model':'output/model.glb'},'review':{'required_views':['iso','front','side','top']},
              'budgets':{'max_materials':3,'max_triangles':30000}}
    (ASSET/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (ASSET/'request.md').write_text('''# Страж кургана / Cairn

Прямой запрос пользователя: выбрать одного босса CubeSiege, воспроизвести геометрию и
крупную воксельную стилистику исходного листа, создать процедурную анимацию, idle,
ходьбу, смерть и читаемые анимации способностей. Выбран Страж кургана, волна 5.
Уточнение пользователя: ассет состоит из кубов без взаимных пересечений; при смерти
рассыпается на кубические камни. Это применяется к source, анимациям и распаду.

Источник: references/selected_cairn.png — неизменённая копия листа с пятью ракурсами.
Лист остаётся candidate; отдельное художественное approval не присваивается.
Сохраняются каменные наплечники/кулаки, ступенчатый гребень, светлая маска,
две янтарные квадратные точки-глаза, три нагрудных печати, серо-зелёные
минеральные пятна и коричневый пояс. Оружие/щит/плащ не добавляются.

Сетка: 0.10 м, X вправо, Y вверх, −Z вперёд; pivot bottom-center. Каждая занятая
ячейка содержит один куб. Цвет — свойство ячейки, отдельные перекрывающиеся
кубы для окраски/декора не создаются. Кубы жёстко привязаны к реальному скелету.
Runtime — один skinned mesh с тремя материалами; кости фрагментов обеспечивают
распад без отдельного runtime Node для каждого вокселя.

Клипы: idle, move, attack_0, attack_1, death. Экспорт −Z forward, метры.
attack_0 = Взрыв вокруг: warning 1.5 с, active 0.30 с, recovery 1.9 с.
attack_1 = Навесная атака: release в начале warning, полёт 1.7 с, active 0.30 с,
recovery 1.6 с. Односекундные action-clips remap фазами игры
0…0.65 / 0.65…0.80 / 0.80…1.0; damage clocks остаются у gameplay.
Procedural SkeletonModifier и отдельная Godot demo проверяют скорость/поворот
и опору стоп. Изменения боевого баланса и замена ассета в game не входят в пакет.
Проверка в standalone Godot demo не является проверкой полного боя CubeSiege.
У существующей игры fade смерти начинается на 75% клипа: интеграция должна
дать увидеть распад и не удалять модель до завершения показа кубических камней.
''',encoding='utf-8')
    print(f'Authored voxel layers: {ASSET}')


if __name__=='__main__': main()
