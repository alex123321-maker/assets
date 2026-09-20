#!/usr/bin/env python3
"""Synchronize generated documentation and build measurements without writing art verdicts."""

import json
from pathlib import Path
from pipeline_reports import write_build_report

ROOT = Path(__file__).resolve().parent.parent
FAMILY_DIR = ROOT / "assets" / "environment" / "destructible_rock"
METRICS_PATH = FAMILY_DIR / "review" / "metrics_summary.json"

STAGE_NAMES = {
    1: ("Stage 1", "Huge intact boulder", 6),
    2: ("Stage 2", "Large broken rock", 3),
    3: ("Stage 3", "Medium remnant", 3),
    4: ("Stage 4", "Small rubble group", 2),
    5: ("Stage 5", "Debris scatter", 3),
}

VARIANT_DESCRIPTIONS = {
    "stage_1_var_1": "Monolith Crag: high summit plateau, eastern shoulder, stepped apron, vertical fissure",
    "stage_1_var_2": "Twin Spire: dual sharp pinnacles with deep canyon cleft and moss in base",
    "stage_1_var_3": "Slanted Wedge: sheer north wall cascading into stepped horizontal sunlit ledges",
    "stage_1_var_4": "Cantilever Brow: jutting overhanging brow with deep undercut shadow cavity",
    "stage_1_var_5": "Three-Lobe Butte: three distinct mountain lobes separated by deep clefts",
    "stage_1_var_6": "Dual Peak Ridge: elongated ridge with twin peaks and central saddle",
    "stage_2_var_1": "Truncated Block: high sheared block dropping sharply to low stepped apron",
    "stage_2_var_2": "Stepped Pyramid Crag: asymmetric tiered rock mass with corner cutouts",
    "stage_2_var_3": "Slanted Core Remnant: angular rock with broken shoulders and fissures",
    "stage_3_var_1": "Triangular Wedge: compact angular rock wedge stepping to base",
    "stage_3_var_2": "Twin Chunk Remnant: two merged rocky masses separated by cleft",
    "stage_3_var_3": "Fractured Stump: squat chunky rock with stepped fractured top",
    "stage_4_var_1": "Fragment & Satellites: main block with two separate satellite chunks",
    "stage_4_var_2": "Triad Debris Cluster: three chunky rock fragments in loose group",
    "stage_5_var_1": "Central Nub & Scatter: one low central stone with 4 small pebbles",
    "stage_5_var_2": "Angular Linear Trail: diagonal trail of 4 separate angular rubble stones",
    "stage_5_var_3": "Crescent Rubble Mound: arc of 4 separate rubble pieces and gravel",
}


def main() -> None:
    if not METRICS_PATH.exists():
        raise FileNotFoundError(f"Missing metrics summary: {METRICS_PATH}")

    metrics_data = json.loads(METRICS_PATH.read_text(encoding="utf-8"))

    # Calculate stage ranges
    stage_ranges = {}
    for st_num in range(1, 6):
        slugs = [s for s in metrics_data if s.startswith(f"stage_{st_num}_")]
        vox = [metrics_data[s]["occupied_voxels"] for s in slugs]
        tris = [metrics_data[s]["triangles"] for s in slugs]
        mats = [metrics_data[s]["materials"] for s in slugs]
        stage_ranges[st_num] = {
            "min_vox": min(vox),
            "max_vox": max(vox),
            "min_tris": min(tris),
            "max_tris": max(tris),
            "max_mats": max(mats),
        }

    # Build per-variant table
    rows = []
    for slug, m in sorted(metrics_data.items()):
        st = int(slug.split("_")[1])
        desc = VARIANT_DESCRIPTIONS.get(slug, slug)
        gx, gy, gz = m["grid"]["x"], m["grid"]["y"], m["grid"]["z"]
        wx = m["world_size"]["x"]
        wy = m["world_size"]["y"]
        wz = m["world_size"]["z"]
        rows.append(
            f"| `{slug}` | {st} | {desc} | {m['occupied_voxels']} | {m['triangles']} | {m['visible_faces']} | {m['materials']} | {gx} x {gy} x {gz} | {wx:.2f} x {wy:.2f} x {wz:.2f} |"
        )

    # 1. Generate README.md
    s1_r = stage_ranges[1]
    s2_r = stage_ranges[2]
    s3_r = stage_ranges[3]
    s4_r = stage_ranges[4]
    s5_r = stage_ranges[5]

    readme_content = f"""# Destructible Voxel Rock Family (Семейство разрушаемых камней)

Семейство статических воксельных ассетов для **Cube Siege** (`voxel_static`), предназначенное для разрушаемых природных ресурсов в игровом мире, с художественной целью соответствовать концепт-арту (`references/rock_concept_reference.png`).

## Концепция стадий и вариантов

Камень имеет **5 визуальных стадий разрушения** (от огромного валуна до россыпи мелких обломков). Переход между стадиями в игре осуществляется через runtime swap с маскировкой коротким VFX разрушения (выброс осколков и каменной пыли).

Формы соседних стадий независимы, что позволяет игре выбирать случайный вариант на каждой стадии.

| Стадия | Игровой смысл | Количество вариантов | Диапазон вокселей | Треугольники | Материалы |
|---|---|:---:|:---:|:---:|:---:|
| **Stage 1** | Огромный целый валун | **6** | {s1_r['min_vox']} – {s1_r['max_vox']} | {s1_r['min_tris']} – {s1_r['max_tris']} | до {s1_r['max_mats']} |
| **Stage 2** | Большой частично разрушенный камень | **3** | {s2_r['min_vox']} – {s2_r['max_vox']} | {s2_r['min_tris']} – {s2_r['max_tris']} | до {s2_r['max_mats']} |
| **Stage 3** | Средний камень / крупный остаток | **3** | {s3_r['min_vox']} – {s3_r['max_vox']} | {s3_r['min_tris']} – {s3_r['max_tris']} | до {s3_r['max_mats']} |
| **Stage 4** | Небольшая группа крупных обломков | **2** | {s4_r['min_vox']} – {s4_r['max_vox']} | {s4_r['min_tris']} – {s4_r['max_tris']} | до {s4_r['max_mats']} |
| **Stage 5** | Россыпь мелких обломков и гальки | **3** | {s5_r['min_vox']} – {s5_r['max_vox']} | {s5_r['min_tris']} – {s5_r['max_tris']} | до {s5_r['max_mats']} |
| **Итого** | | **17** | | | |

## Палитра материалов (PBR)

Все ассеты используют палитру из 4 материалов, откалиброванную по утверждённому концепт-арту:
1. `stone_primary` (S): основной корпус камня, тёплый серый оттенок (#7d7872).
2. `stone_dark` (D): глубокие расщелины, выемки под нависаниями, контактные тени (#555350).
3. `stone_light` (L): верхние освещённые солнцем плоскости, гребни и террасы (#aea8a0).
4. `stone_moss` (M): деликатные островки мха в укрытых расщелинах и нишах (#6e7252).

## Разнообразие силуэтов Stage 1

1. `stage_1_var_1` — **Monolith Crag**: Высокая главная каменная башня на западе с плоской вершиной, восточное плечо, ступенчатый передний шлейф.
2. `stage_1_var_2` — **Twin Spire**: Сдвоенная масса из двух обособленных утёсов разной высоты с глубоким V-образным каньоном.
3. `stage_1_var_3` — **Slanted Wedge**: Обрывистая северная стена и каскад пологих горизонтальных террас к югу.
4. `stage_1_var_4` — **Cantilever Brow**: Массивный нависающий лоб с глубокой теневой полостью под ним и ступенчатым восточным склоном.
5. `stage_1_var_5` — **Three-Lobe Butte**: Трёхглавый массив с выраженными расщелинами между всеми тремя лопастями.
6. `stage_1_var_6` — **Dual Peak Ridge**: Продолговатый хребет с двумя вершинами и седловиной между ними.

## Структура пакета

```text
assets/environment/destructible_rock/
├── README.md
├── references/
│   └── rock_concept_reference.png
├── review/
│   ├── contact_sheet.png
│   ├── reference_vs_3d_comparison.png
│   ├── stage_1_comparison.png
│   ├── metrics_summary.json
│   └── review.md
├── stage_1_var_1/ ... stage_1_var_6/
├── stage_2_var_1/ ... stage_2_var_3/
├── stage_3_var_1/ ... stage_3_var_2/
├── stage_4_var_1/ ... stage_4_var_2/
└── stage_5_var_1/ ... stage_5_var_3/
```

Каждый вариант содержит:
- `manifest.json` — метаданные, тип `voxel_static`, бюджеты (max 4 materials, max 5000 tris);
- `request.md` — описание варианта;
- `source/voxels.json` — канонический воксельный источник;
- `output/model.glb` — готовый для Godot меш;
- `review/` — ракурсы (`iso`, `front`, `side`, `top`), `metrics.json`, `review.md`.
"""

    (FAMILY_DIR / "README.md").write_text(readme_content, encoding="utf-8")
    print("Updated README.md successfully.")

    # 2. Generate build measurements; preserve authored review.

    write_build_report(FAMILY_DIR / "review", "Destructible rock family", json.loads(METRICS_PATH.read_text(encoding="utf-8")))



if __name__ == "__main__":
    main()
