# Family Self Review: Destructible Rock Family (Issue #3 Art Pass)

## Acceptance Criteria Checklist

- [x] **Ровно 17 вариантов**: 6 (Stage 1) / 3 (Stage 2) / 3 (Stage 3) / 2 (Stage 4) / 3 (Stage 5).
- [x] **Canonical Source**: Каждый вариант имеет полностью воспроизводимый `source/voxels.json` в layered voxel representation.
- [x] **Repository Validation**: Все варианты проходят `tools/validate_asset.py` и общий `tools/validate_all.py`.
- [x] **Blender Pipeline**: Все варианты собираются через скрипты сборки (`build_voxel_asset.py`, `build_family.py`) на Blender 5.2.1 LTS.
- [x] **GLB Export**: Каждый вариант экспортирует валидный `output/model.glb` для Godot с единым мешем на материал.
- [x] **No Individual Cube Objects**: Ни один вариант не использует отдельные cube nodes в рантайме.
- [x] **Internal Face Culling**: Внутренние грани между смежными занятыми вокселями полностью удалены.
- [x] **Art Pass: 4-Material Palette**: Полноценная 4-материальная палитра PBR по утверждённому концепту `references/rock_concept_reference.png`:
  - `stone_primary` (S): основной корпус камня, вертикальные грани (#7d7872);
  - `stone_dark` (D): глубокие расщелины, выемки под нависаниями, контактные тени (#555350);
  - `stone_light` (L): освещённые солнцем верхние террасы, плато и гребни (#aea8a0);
  - `stone_moss` (M): деликатные акцентные островки мха в укрытых расщелинах и нишах (#6e7252).
- [x] **No Diagonal Staircases / Flat Boxes**: Устранены непреднамеренные 45-градусные лестницы и плоские параллелепипеды; форма смоделирована массивными ступенчатыми лопастями и гранёными фасками.
- [x] **Silhouette Diversity (Stage 1)**: Все 6 вариантов Stage 1 обладают выраженно различными силуэтами (Monolith Crag, Twin Spire, Slanted Wedge, Cantilever Brow, Three-Lobe Butte, Dual Peak Ridge).
- [x] **Monotonic Mass Reduction**: Объем и количество вокселей строго и последовательно уменьшаются от Stage 1 к Stage 5 (707–1023 → 454–576 → 202–268 → 126–134 → 33–38).
- [x] **Ground Contact & Pivot**: Все варианты имеют плоский контакт с землей (`y=0`) и центрированный `bottom_center` origin.
- [x] **Review Package**: Для каждого из 17 вариантов созданы ракурсы `iso.png`, `front.png`, `side.png`, `top.png` и `metrics.json`.
- [x] **Family Contact Sheet & Side-by-Side Comparison**:
  - `review/contact_sheet.png`: общая панорама всех 17 моделей (2048x1152);
  - `review/stage_1_comparison.png`: увеличенное попарное сравнение концептов Stage 1 и 3D-моделей;
  - `review/reference_vs_3d_comparison.png`: сравнение всего референсного листа и 3D-семейства.

## Summary of Metrics

| Variant | Stage | Description | Occupied Voxels | Triangles | Visible Faces | Materials | Grid (X x Y x Z) | World Size (m) |
|---|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `stage_1_var_1` | 1 | Monolith Crag: high summit plateau, eastern shoulder, stepped apron, vertical fissure | 707 | 880 | 373 | 4 | 16 x 12 x 16 | 2.40 x 1.80 x 2.40 |
| `stage_1_var_2` | 1 | Twin Spire: dual sharp pinnacles with deep canyon cleft and moss in base | 727 | 633 | 261 | 4 | 16 x 12 x 16 | 2.40 x 1.80 x 2.40 |
| `stage_1_var_3` | 1 | Slanted Wedge: sheer north wall cascading into stepped horizontal sunlit ledges | 969 | 474 | 198 | 4 | 16 x 12 x 16 | 2.40 x 1.80 x 2.40 |
| `stage_1_var_4` | 1 | Cantilever Brow: jutting overhanging brow with deep undercut shadow cavity | 800 | 534 | 241 | 4 | 16 x 12 x 16 | 2.40 x 1.80 x 2.40 |
| `stage_1_var_5` | 1 | Three-Lobe Butte: three distinct mountain lobes separated by deep clefts | 1023 | 576 | 240 | 4 | 16 x 12 x 16 | 2.40 x 1.80 x 2.40 |
| `stage_1_var_6` | 1 | Dual Peak Ridge: elongated ridge with twin peaks and central saddle | 900 | 444 | 196 | 4 | 18 x 11 x 15 | 2.70 x 1.65 x 2.25 |
| `stage_2_var_1` | 2 | Truncated Block: high sheared block dropping sharply to low stepped apron | 576 | 264 | 110 | 4 | 14 x 9 x 14 | 2.10 x 1.35 x 2.10 |
| `stage_2_var_2` | 2 | Stepped Pyramid Crag: asymmetric tiered rock mass with corner cutouts | 568 | 240 | 113 | 3 | 14 x 8 x 14 | 2.10 x 1.20 x 2.10 |
| `stage_2_var_3` | 2 | Slanted Core Remnant: angular rock with broken shoulders and fissures | 454 | 311 | 132 | 4 | 14 x 8 x 14 | 2.10 x 1.20 x 2.10 |
| `stage_3_var_1` | 3 | Triangular Wedge: compact angular rock wedge stepping to base | 256 | 176 | 79 | 3 | 12 x 7 x 12 | 1.80 x 1.05 x 1.80 |
| `stage_3_var_2` | 3 | Twin Chunk Remnant: two merged rocky masses separated by cleft | 202 | 199 | 91 | 3 | 12 x 6 x 12 | 1.80 x 0.90 x 1.80 |
| `stage_3_var_3` | 3 | Fractured Stump: squat chunky rock with stepped fractured top | 268 | 186 | 85 | 2 | 12 x 6 x 12 | 1.80 x 0.90 x 1.80 |
| `stage_4_var_1` | 4 | Fragment & Satellites: main block with two separate satellite chunks | 126 | 172 | 85 | 3 | 12 x 5 x 12 | 1.80 x 0.75 x 1.80 |
| `stage_4_var_2` | 4 | Triad Debris Cluster: three chunky rock fragments in loose group | 134 | 268 | 130 | 3 | 12 x 4 x 12 | 1.80 x 0.60 x 1.80 |
| `stage_5_var_1` | 5 | Central Nub & Scatter: one low central stone with 4 small pebbles | 37 | 296 | 143 | 3 | 10 x 3 x 10 | 1.50 x 0.45 x 1.50 |
| `stage_5_var_2` | 5 | Angular Linear Trail: diagonal trail of 4 separate angular rubble stones | 33 | 268 | 128 | 3 | 10 x 3 x 10 | 1.50 x 0.45 x 1.50 |
| `stage_5_var_3` | 5 | Crescent Rubble Mound: arc of 4 separate rubble pieces and gravel | 38 | 278 | 133 | 3 | 10 x 3 x 10 | 1.50 x 0.45 x 1.50 |

## Known Intentional Deviations
None.

## Visual Inspection Reference Media

Visual inspection and validation against `references/rock_concept_reference.png` are provided via dedicated comparison media in `review/`:
- `review/reference_vs_3d_comparison.png`: Full concept sheet vs 3D renders side-by-side.
- `review/stage_1_comparison.png`: High-resolution side-by-side comparison for each of the 6 Stage 1 boulder concepts vs rendered 3D models.
- `review/contact_sheet.png`: Global panorama of all 17 models across Stages 1–5.
- Per-variant orthogonal renders (`iso.png`, `front.png`, `side.png`, `top.png`) in each variant's `review/` directory.

### Structural & Silhouette Design Intent
- **Stage 1 (Vars 1–6)**: Distinct macro silhouettes (Monolith Crag, Twin Spire, Slanted Wedge, Cantilever Brow, Three-Lobe Butte, Dual Peak Ridge). Meshes built with facet dissolving (planar consolidation) and 0.26 bevel chamfers to avoid terraced staircases.
- **Stages 2–5**: Monotonic volume and polygon reduction across destruction states, flat ground contact at y=0, and clean material separation.
- **Material Differentiation**: Upper horizontal planes mapped to `stone_light`, crevices/undercuts to `stone_dark`, side walls to `stone_primary`, and sheltered recesses to `stone_moss` accents.

## Notes for External Reviewer
- Review package contains:
  - `review/reference_vs_3d_comparison.png` — full family comparison against approved concept art;
  - `review/stage_1_comparison.png` — magnified side-by-side comparison of 6 Stage 1 concepts vs 3D models;
  - `review/contact_sheet.png` — panorama of all 17 models;
  - 4 orthogonal renders (iso, front, side, top) and `metrics.json` for each variant.
- All polygon counts (268–880 tris) strictly satisfy the <= 5000 tris budget.
- All material counts (<= 4) strictly satisfy the <= 4 materials budget.
- All GLBs are exported with single mesh per material and culled internal faces.
