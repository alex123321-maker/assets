# Terrain Material Kit (Набор материалов террейна)

Единый production-ready набор стилизованных воксельных материалов террейна для **Cube Siege** (`alex123321-maker/assets`), заменяющий прототипные процедурные 16×16 runtime-текстуры из `scripts/map_generator.gd` (Issue #6).

Набор приводит поверхность процедурного мира в соответствие с утверждённым визуальным направлением игры, разрушаемыми скалами (`destructible_rock`, Issue #3) и дубовыми деревьями (`tree_oak`, Issue #5).

---

## 1. Состав набора поверхностей

Набор включает 4 основных типа поверхностей биомов плюс вспомогательный подпочвенный материал:

| Поверхность | Роль в мире / Биом | Разрешение | Шероховатость (PBR) | Ключевая палитра | Описание визуального характера |
|---|---|:---:|:---:|:---:|---|
| **Forest Grass Top** | Лесной биом (верхняя грань) | 16×16 | 0.85 | `#28501b`, `#346323`, `#447b2c` | Насыщенный глубокий зелёный, крупномасштабная плавная кластеризация; гармонирует с кронами дубов. |
| **Plains Meadow Top** | Луговой биом (верхняя грань) | 16×16 | 0.85 | `#487425`, `#5b8d2e`, `#70a338` | Светлее и теплее леса; спокойное солнечное луговое ощущение с деликатными золотистыми крапинками. |
| **Mountain Stone Top** | Горный биом (верхняя грань) | 16×16 | 0.90 | `#7d7872`, `#959088`, `#aea8a0` | Светло/средне-серый стилизованный гранит с читаемыми фасетами; 100% совместим с `destructible_rock`. |
| **Cliff / Rock Side** | Скальные обрывы (боковые грани) | 16×16 | 0.92 | `#44413e`, `#54504c`, `#746e67` | Темнее верха; нерегулярные горизонтальные пласты со ступенчатыми сколами; глубина перепадов рельефа. |
| **Soil / Dirt Accent** | Подпочва / срезы берегов | 16×16 | 0.92 | `#5a402b`, `#6e4f35`, `#845f40` | Тёплый богатый суглинок, естественные комья; поддёрновые переходы и тропы. |

---

## 2. Атлас текстур (Single Draw Call Atlas)

Для оптимизации отрисовки чанков и минимизации draw calls текстуры объединены в единый 64×64 RGBA8 Texture Atlas (`textures/terrain_atlas.png`). Атлас организован в сетку 4×4 ячейки по 16×16 текселей:

```text
       X=0..15              X=16..31             X=32..47             X=48..63
    ┌────────────────────┬────────────────────┬────────────────────┬────────────────────┐
Y=0 │ Forest Grass Top   │ Plains Meadow Top  │ Mountain Stone Top │ Cliff Rock Side    │
    │ [0.00, 0.00, 0.25] │ [0.25, 0.00, 0.50] │ [0.50, 0.00, 0.75] │ [0.75, 0.00, 1.00] │
    ├────────────────────┼────────────────────┼────────────────────┼────────────────────┤
Y=1 │ Soil / Dirt Accent │ Forest Bank Side   │ Plains Bank Side   │ Stone Cliff Rim    │
    │ [0.00, 0.25, 0.50] │ [0.25, 0.25, 0.50] │ [0.50, 0.25, 0.75] │ [0.75, 0.25, 1.00] │
    ├────────────────────┼────────────────────┼────────────────────┼────────────────────┤
Y=2 │ Rocky Dirt Path    │ Forest Path Wear   │ Mountain Scree     │ Deep Cliff Shaded  │
    │ [0.00, 0.50, 0.75] │ [0.25, 0.50, 0.75] │ [0.50, 0.50, 0.75] │ [0.75, 0.50, 1.00] │
    ├────────────────────┼────────────────────┼────────────────────┼────────────────────┤
Y=3 │ Mossy Rock Variant │ Dry Sunny Grass    │ Dense Dark Earth   │ Cliff Crest Lip    │
    │ [0.00, 0.75, 1.00] │ [0.25, 0.75, 1.00] │ [0.50, 0.75, 1.00] │ [0.75, 0.75, 1.00] │
    └────────────────────┴────────────────────┴────────────────────┴────────────────────┘
```

### Координаты всех 16 регионов (UV Bounding Boxes):
- **Строка 0 (Основные поверхности)**:
  - **Forest Grass Top**: `u: [0.00, 0.25]`, `v: [0.00, 0.25]`
  - **Plains Meadow Top**: `u: [0.25, 0.50]`, `v: [0.00, 0.25]`
  - **Mountain Stone Top**: `u: [0.50, 0.75]`, `v: [0.00, 0.25]`
  - **Cliff Rock Side**: `u: [0.75, 1.00]`, `v: [0.00, 0.25]`
- **Строка 1 (Подпочва и кромки переходов)**:
  - **Soil / Dirt Accent**: `u: [0.00, 0.25]`, `v: [0.25, 0.50]`
  - **Forest Bank Side Edge**: `u: [0.25, 0.50]`, `v: [0.25, 0.50]`
  - **Plains Bank Side Edge**: `u: [0.50, 0.75]`, `v: [0.25, 0.50]`
  - **Stone Cliff Rim**: `u: [0.75, 1.00]`, `v: [0.25, 0.50]`
- **Строка 2 (Вторичные тропы и осыпи)**:
  - **Rocky Dirt Path**: `u: [0.00, 0.25]`, `v: [0.50, 0.75]`
  - **Forest Path Wear**: `u: [0.25, 0.50]`, `v: [0.50, 0.75]`
  - **Mountain Scree**: `u: [0.50, 0.75]`, `v: [0.50, 0.75]`
  - **Deep Cliff Shaded**: `u: [0.75, 1.00]`, `v: [0.50, 0.75]`
- **Строка 3 (Акцентные вариации биомов)**:
  - **Mossy Rock Variant**: `u: [0.00, 0.25]`, `v: [0.75, 1.00]`
  - **Dry Sunny Grass**: `u: [0.25, 0.50]`, `v: [0.75, 1.00]`
  - **Dense Dark Earth**: `u: [0.50, 0.75]`, `v: [0.75, 1.00]`
  - **Cliff Crest Lip**: `u: [0.75, 1.00]`, `v: [0.75, 1.00]`

---

## 3. Интеграция в Godot 4.x

### Вариант А: Индивидуальные материалы чанка (Drop-in замена `scripts/map_generator.gd`)

В `scripts/map_generator.gd` функция `setup_materials()` заменяется загрузкой готовых материалов:

```gdscript
func setup_materials() -> void:
	mat_forest = preload("res://assets/environment/terrain_materials/textures/material_forest.tres")
	mat_plains = preload("res://assets/environment/terrain_materials/textures/material_plains.tres")
	mat_mountains = preload("res://assets/environment/terrain_materials/textures/material_mountains.tres")
	mat_cliff = preload("res://assets/environment/terrain_materials/textures/material_cliff.tres")
```

Либо программно с назначением текстур:

```gdscript
func setup_materials() -> void:
	mat_forest = _create_terrain_mat("res://assets/environment/terrain_materials/textures/forest_grass_top.png", 0.85)
	mat_plains = _create_terrain_mat("res://assets/environment/terrain_materials/textures/plains_meadow_top.png", 0.85)
	mat_mountains = _create_terrain_mat("res://assets/environment/terrain_materials/textures/mountain_stone_top.png", 0.90)
	mat_cliff = _create_terrain_mat("res://assets/environment/terrain_materials/textures/cliff_side.png", 0.92)

func _create_terrain_mat(tex_path: String, rough: float) -> StandardMaterial3D:
	var mat: StandardMaterial3D = StandardMaterial3D.new()
	mat.albedo_texture = load(tex_path)
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	mat.roughness = rough
	mat.cull_mode = BaseMaterial3D.CULL_BACK
	return mat
```

### Вариант Б: Единый атлас для 1 Draw Call на чанк (`material_terrain_atlas.tres`)

При использовании атласа в `ChunkBuilder`:
- Все воксельные полигоны чанка (Forest, Plains, Mountain, Cliff, Dirt) отправляются в один `SurfaceTool` с материалом `material_terrain_atlas.tres`.
- UV-координаты каждой грани масштабируются на `0.25` со смещением в соответствующую ячейку атласа:
  - `uv = uv_base * 0.25 + cell_offset`
- Это сводит число draw calls до **1 вызова на чанк**!

---

## 4. Структура пакета ассета

```text
assets/environment/terrain_materials/
├── README.md                               # Данная документация
├── references/
│   ├── README.md                           # Описание референса и visual contract
│   └── terrain_concept_reference.png       # Утверждённый концепт-арт и спецификации
├── textures/ (и output/)
│   ├── forest_grass_top.png                # 16x16 RGBA8
│   ├── plains_meadow_top.png               # 16x16 RGBA8
│   ├── mountain_stone_top.png              # 16x16 RGBA8
│   ├── cliff_side.png                      # 16x16 RGBA8
│   ├── dirt_soil.png                       # 16x16 RGBA8
│   ├── terrain_atlas.png                   # 64x64 RGBA8 (16 регионов)
│   ├── material_forest.tres                # Godot StandardMaterial3D
│   ├── material_plains.tres                # Godot StandardMaterial3D
│   ├── material_mountains.tres             # Godot StandardMaterial3D
│   ├── material_cliff.tres                 # Godot StandardMaterial3D
│   ├── material_dirt.tres                  # Godot StandardMaterial3D
│   └── material_terrain_atlas.tres         # Godot StandardMaterial3D (Atlas)
├── source/
│   ├── palette.json                        # Цветовые константы палитр
│   └── textures_source.json                # ASCII матрицы и разметка атласа
├── review/
│   ├── contact_sheet.png                   # Полный обзор всех материалов и рендеров
│   ├── comparison_sheet.png                # Попиксельное и 3D сопоставление биомов
│   ├── reference_vs_3d_comparison.png      # Референс vs 3D игровой кадр
│   ├── gameplay_mockup.png                 # Игровая камера с деревьями и камнями
│   ├── tileability_forest_grass_top.png    # 6x6 бесшовный тест тайлинга
│   ├── tileability_plains_meadow_top.png   # 6x6 бесшовный тест тайлинга
│   ├── tileability_mountain_stone_top.png  # 6x6 бесшовный тест тайлинга
│   ├── tileability_cliff_side.png          # 6x6 бесшовный тест тайлинга
│   ├── tileability_dirt_soil.png           # 6x6 бесшовный тест тайлинга
│   ├── metrics_summary.json                # Сводные метрики пакета
│   └── review.md                           # Самоанализ и критерии приёмки
├── block_forest_grass/                     # 3D воксельный showcase-блок (voxel_static)
├── block_plains_meadow/                    # 3D воксельный showcase-блок (voxel_static)
├── block_mountain_stone/                   # 3D воксельный showcase-блок (voxel_static)
├── block_cliff_strata/                     # 3D воксельный showcase-блок (voxel_static)
└── block_dirt_soil/                        # 3D воксельный showcase-блок (voxel_static)
```

Каждый showcase-блок является валидным пакетом `voxel_static` и представляет собой стандартный 1.0м воксельный куб, оттекстурированный реальными 16×16 PNG текстурами пакета с точечной фильтрацией (`TEXTURE_FILTER_NEAREST`), стандартной UV-разметкой и PBR matte параметрами. Пакет содержит `manifest.json`, `request.md`, `source/voxels.json`, `output/model.glb` (с текстурами) и `review/` с 4 ортогональными рендерами (iso, front, side, top 512×512) и `metrics.json`.
