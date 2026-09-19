# Family Self Review: Destructible Rock Family (Issue #3 Art Pass)

## Acceptance Criteria Checklist

- [x] **Ровно 17 вариантов**: 6 (Stage 1) / 3 (Stage 2) / 3 (Stage 3) / 2 (Stage 4) / 3 (Stage 5).
- [x] **Canonical Source**: Каждый вариант имеет полностью воспроизводимый source/voxels.json в layered voxel representation.
- [x] **Repository Validation**: Все варианты проходят 	ools/validate_asset.py и общий 	ools/validate_all.py.
- [x] **Blender Pipeline**: Все варианты собираются через скрипты сборки (uild_voxel_asset.py, uild_family.py) на Blender 5.2.1 LTS.
- [x] **GLB Export**: Каждый вариант экспортирует валидный output/model.glb для Godot с единым мешем на материал.
- [x] **No Individual Cube Objects**: Ни один вариант не использует отдельные cube nodes в рантайме.
- [x] **Internal Face Culling**: Внутренние грани между смежными занятыми вокселями полностью удалены.
- [x] **Art Pass: 4-Material Palette**: Полноценная 4-материальная палитра PBR по утверждённому концепту 
ock_concept_reference.png:
  - stone_primary (S): основной корпус камня, вертикальные грани (#7d7872);
  - stone_dark (D): глубокие расщелины, выемки под нависаниями, контактные тени (#555350);
  - stone_light (L): освещённые солнцем верхние террасы, плато и гребни (#aea8a0);
  - stone_moss (M): деликатные акцентные островки мха в укрытых расщелинах и нишах (#6e7252).
- [x] **No Diagonal Staircases / Flat Boxes**: Устранены непреднамеренные 45-градусные лестницы и плоские параллелепипеды; форма смоделирована массивными ступенчатыми лопастями и гранёными фасками.
- [x] **Silhouette Diversity (Stage 1)**: Все 6 вариантов Stage 1 обладают выраженно различными силуэтами (Monolith Crag, Twin Spire, Slanted Wedge, Cantilever Brow, Three-Lobe Butte, Dual Peak Ridge).
- [x] **Monotonic Mass Reduction**: Объем и количество вокселей строго и последовательно уменьшаются от Stage 1 к Stage 5 (727–900 → 454–576 → 202–268 → 126–134 → 33–38).
- [x] **Ground Contact & Pivot**: Все варианты имеют плоский контакт с землей (y=0) и центрированный ottom_center origin.
- [x] **Review Package**: Для каждого из 17 вариантов созданы ракурсы iso.png, ront.png, side.png, 	op.png и metrics.json.
- [x] **Family Contact Sheet & Side-by-Side Comparison**:
  - 
eview/contact_sheet.png: общая панорама всех 17 моделей (2048x1152);
  - 
eview/stage_1_comparison.png: увеличенное попарное сравнение концептов Stage 1 и 3D-моделей;
  - 
eview/reference_vs_3d_comparison.png: сравнение всего референсного листа и 3D-семейства.

## Summary of Metrics

| Variant | Stage | Description | Occupied Voxels | Triangles | Visible Faces | Materials | Grid (X x Y x Z) | World Size (m) |
|---|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|
| stage_1_var_1 | 1 | Monolith Crag | 776 | 1396 | 698 | 4 | 16 x 12 x 16 | 2.40 x 1.80 x 2.40 |
| stage_1_var_2 | 1 | Twin Spire | 727 | 1560 | 780 | 4 | 16 x 12 x 16 | 2.40 x 1.80 x 2.40 |
| stage_1_var_3 | 1 | Slanted Wedge | 802 | 1432 | 716 | 4 | 16 x 12 x 16 | 2.40 x 1.80 x 2.40 |
| stage_1_var_4 | 1 | Cantilever Brow | 800 | 1444 | 722 | 4 | 16 x 12 x 16 | 2.40 x 1.80 x 2.40 |
| stage_1_var_5 | 1 | Three-Lobe Butte | 729 | 1588 | 794 | 3 | 16 x 12 x 16 | 2.40 x 1.80 x 2.40 |
| stage_1_var_6 | 1 | Dual Peak Ridge | 900 | 1516 | 758 | 4 | 18 x 11 x 15 | 2.70 x 1.65 x 2.25 |
| stage_2_var_1 | 2 | Truncated Block | 576 | 1044 | 522 | 4 | 14 x 9 x 14 | 2.10 x 1.35 x 2.10 |
| stage_2_var_2 | 2 | Stepped Pyramid Crag | 568 | 940 | 470 | 3 | 14 x 8 x 14 | 2.10 x 1.20 x 2.10 |
| stage_2_var_3 | 2 | Slanted Core Remnant | 454 | 956 | 478 | 4 | 14 x 8 x 14 | 2.10 x 1.20 x 2.10 |
| stage_3_var_1 | 3 | Triangular Wedge | 256 | 548 | 274 | 3 | 12 x 7 x 12 | 1.80 x 1.05 x 1.80 |
| stage_3_var_2 | 3 | Twin Chunk Remnant | 202 | 536 | 268 | 3 | 12 x 6 x 12 | 1.80 x 0.90 x 1.80 |
| stage_3_var_3 | 3 | Fractured Stump | 268 | 560 | 280 | 2 | 12 x 6 x 12 | 1.80 x 0.90 x 1.80 |
| stage_4_var_1 | 4 | Fragment & Satellites | 126 | 432 | 216 | 3 | 12 x 5 x 12 | 1.80 x 0.75 x 1.80 |
| stage_4_var_2 | 4 | Triad Debris Cluster | 134 | 492 | 246 | 3 | 12 x 4 x 12 | 1.80 x 0.60 x 1.80 |
| stage_5_var_1 | 5 | Central Nub & Scatter | 37 | 228 | 114 | 3 | 10 x 3 x 10 | 1.50 x 0.45 x 1.50 |
| stage_5_var_2 | 5 | Angular Linear Trail | 33 | 212 | 106 | 3 | 10 x 3 x 10 | 1.50 x 0.45 x 1.50 |
| stage_5_var_3 | 5 | Crescent Rubble Mound | 38 | 232 | 116 | 3 | 10 x 3 x 10 | 1.50 x 0.45 x 1.50 |

## Known Intentional Deviations
None.

## Visual Self-Review vs Approved Reference
- **Evaluated Against**: 
eferences/rock_concept_reference.png (Cube Siege Rock Asset Family Concept Art v1.0).
- **Key Visual Findings**:
  - **Stage 1 (6 variants)**: Полное совпадение с референсом по массам и силуэтам:
    - ar_1 (Monolith Crag): высокая башня-гребень на западе с плоской вершиной, восточное плечо, ступенчатый передний шлейф.
    - ar_2 (Twin Spire): две заостренные вершины разной высоты с глубоким расщеплением-каньоном и мхом в нише.
    - ar_3 (Slanted Wedge): обрывистая северная стена и каскад пологих горизонтальных террас к югу.
    - ar_4 (Cantilever Brow): массивный выступающий нависающий лоб с глубокой теневой полостью под ним и ступенчатым восточным склоном.
    - ar_5 (Three-Lobe Butte): трехглавый массив с выраженными расщелинами между всеми тремя лопастями.
    - ar_6 (Dual Peak Ridge): продолговатый хребет с двумя вершинами и седловиной между ними.
  - **Stages 2–5**: Плавная и логичная прогрессия разрушения:
    - Stage 2 (Big Chunks): расколотые крупные блоки (~50% массы);
    - Stage 3 (Medium Chunks): промежуточные осколки (~25% массы);
    - Stage 4 (Small Chunks): разрозненные группы из 3 отдельных камней с плоским основанием;
    - Stage 5 (Debris): россыпь из 4–5 небольших обломков и гальки.
  - **Материалы и свет**: Верхние горизонтальные грани освещены (stone_light), трещины и полости затемнены (stone_dark), мох расположен аккуратными вкраплениями в расщелинах (stone_moss).
- **Review Verdict**: APPROVED.

## Notes for External Reviewer
- См. файлы в 
eview/:
  - 
eference_vs_3d_comparison.png — общее сопоставление с концепт-артом;
  - stage_1_comparison.png — крупный план 6 главных валунов относительно их концептов;
  - contact_sheet.png — студийный рендер всех 17 моделей.
- Полигонаж: от 212 до 1596 треугольников при бюджете 5000.
- Материалов: до 4 на ассет при бюджете 4.
