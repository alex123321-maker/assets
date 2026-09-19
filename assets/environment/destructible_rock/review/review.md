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
- [x] **Monotonic Mass Reduction**: Объем и количество вокселей строго и последовательно уменьшаются от Stage 1 к Stage 5 (727–900 → 454–576 → 202–268 → 126–134 → 33–38).
- [x] **Ground Contact & Pivot**: Все варианты имеют плоский контакт с землей (`y=0`) и центрированный `bottom_center` origin.
- [x] **Review Package**: Для каждого из 17 вариантов созданы ракурсы `iso.png`, `front.png`, `side.png`, `top.png` и `metrics.json`.
- [x] **Family Contact Sheet & Side-by-Side Comparison**:
  - `review/contact_sheet.png`: общая панорама всех 17 моделей (2048x1152);
  - `review/stage_1_comparison.png`: увеличенное попарное сравнение концептов Stage 1 и 3D-моделей;
  - `review/reference_vs_3d_comparison.png`: сравнение всего референсного листа и 3D-семейства.

## Summary of Metrics

| Variant | Stage | Description | Occupied Voxels | Triangles | Visible Faces | Materials | Grid (X x Y x Z) | World Size (m) |
|---|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `stage_1_var_1` | 1 | Monolith Crag: high summit plateau, eastern shoulder, stepped apron, vertical fissure | 776 | 2112 | 1048 | 4 | 16 x 12 x 16 | 2.40 x 1.80 x 2.40 |
| `stage_1_var_2` | 1 | Twin Spire: dual sharp pinnacles with deep canyon cleft and moss in base | 727 | 2295 | 1131 | 4 | 16 x 12 x 16 | 2.40 x 1.80 x 2.40 |
| `stage_1_var_3` | 1 | Slanted Wedge: sheer north wall cascading into stepped horizontal sunlit ledges | 802 | 2060 | 1007 | 4 | 16 x 12 x 16 | 2.40 x 1.80 x 2.40 |
| `stage_1_var_4` | 1 | Cantilever Brow: jutting overhanging brow with deep undercut shadow cavity | 800 | 2134 | 1056 | 4 | 16 x 12 x 16 | 2.40 x 1.80 x 2.40 |
| `stage_1_var_5` | 1 | Three-Lobe Butte: three distinct mountain lobes separated by deep clefts | 729 | 2239 | 1106 | 3 | 16 x 12 x 16 | 2.40 x 1.80 x 2.40 |
| `stage_1_var_6` | 1 | Dual Peak Ridge: elongated ridge with twin peaks and central saddle | 900 | 2184 | 1064 | 4 | 18 x 11 x 15 | 2.70 x 1.65 x 2.25 |
| `stage_2_var_1` | 2 | Truncated Block: high sheared block dropping sharply to low stepped apron | 576 | 1454 | 710 | 4 | 14 x 9 x 14 | 2.10 x 1.35 x 2.10 |
| `stage_2_var_2` | 2 | Stepped Pyramid Crag: asymmetric tiered rock mass with corner cutouts | 568 | 1306 | 642 | 3 | 14 x 8 x 14 | 2.10 x 1.20 x 2.10 |
| `stage_2_var_3` | 2 | Slanted Core Remnant: angular rock with broken shoulders and fissures | 454 | 1359 | 666 | 4 | 14 x 8 x 14 | 2.10 x 1.20 x 2.10 |
| `stage_3_var_1` | 3 | Triangular Wedge: compact angular rock wedge stepping to base | 256 | 784 | 387 | 3 | 12 x 7 x 12 | 1.80 x 1.05 x 1.80 |
| `stage_3_var_2` | 3 | Twin Chunk Remnant: two merged rocky masses separated by cleft | 202 | 789 | 395 | 3 | 12 x 6 x 12 | 1.80 x 0.90 x 1.80 |
| `stage_3_var_3` | 3 | Fractured Stump: squat chunky rock with stepped fractured top | 268 | 820 | 402 | 2 | 12 x 6 x 12 | 1.80 x 0.90 x 1.80 |
| `stage_4_var_1` | 4 | Fragment & Satellites: main block with two separate satellite chunks | 126 | 668 | 332 | 3 | 12 x 5 x 12 | 1.80 x 0.75 x 1.80 |
| `stage_4_var_2` | 4 | Triad Debris Cluster: three chunky rock fragments in loose group | 134 | 820 | 398 | 3 | 12 x 4 x 12 | 1.80 x 0.60 x 1.80 |
| `stage_5_var_1` | 5 | Central Nub & Scatter: one low central stone with 4 small pebbles | 37 | 472 | 237 | 3 | 10 x 3 x 10 | 1.50 x 0.45 x 1.50 |
| `stage_5_var_2` | 5 | Angular Linear Trail: diagonal trail of 4 separate angular rubble stones | 33 | 438 | 219 | 3 | 10 x 3 x 10 | 1.50 x 0.45 x 1.50 |
| `stage_5_var_3` | 5 | Crescent Rubble Mound: arc of 4 separate rubble pieces and gravel | 38 | 472 | 233 | 3 | 10 x 3 x 10 | 1.50 x 0.45 x 1.50 |

## Known Intentional Deviations
None.

## Visual Self-Review vs Approved Reference

Оценка произведена человеком/агентом путём визуального сравнения сгенерированных рендеров (`review/reference_vs_3d_comparison.png`, `review/stage_1_comparison.png` и индивидуальных `iso.png`) с концепт-артом `references/rock_concept_reference.png`:

### 1. Анализ силуэтов и масс Stage 1
- **`stage_1_var_1` (Monolith Crag)**:
  - Референс: доминирующая башня с плоской наклонной вершиной, пониженное восточное плечо, ступенчатый передний шлейф.
  - 3D Pass: высокая западная башня (y=11) с широким плато `L`, восточный контрфорс (y=7) и вертикальная щель-расщелина между ними. Силуэт совпадает.
- **`stage_1_var_2` (Twin Spire)**:
  - Референс: два острых пика разной высоты с глубоким V-образным расщеплением до основания и мхом в глубине трещины.
  - 3D Pass: пики (y=12 и y=10) с каньоном шириной в 1–2 вокселя, полом со мхом `M` в основании расщелины. Чёткая узнаваемость.
- **`stage_1_var_3` (Slanted Wedge)**:
  - Референс: отвесный северный срез и широкие пологие горизонтальные террасы, каскадом спускающиеся к югу.
  - 3D Pass: задняя стена высотой 11 вокселей, каскадные террасы (высоты 8, 5, 2) с освещёнными поверхностями `L` и мхом вдоль стыка террас.
- **`stage_1_var_4` (Cantilever Brow)**:
  - Референс: нависающий массивный лоб на переднем плане с глубокой тенью под ним.
  - 3D Pass: консольный выступ (y=4..7) с полостью поднутрения (y=0..2) из тёмного камня `D`, ступенчатый подъём к вершине башни.
- **`stage_1_var_5` (Three-Lobe Butte)**:
  - Референс: три раздельные горные лопасти (задний пик, левый и правый контрфорсы) с глубокими щелями между ними.
  - 3D Pass: центральный пик (y=11) и два боковых массива (y=8), разделенные продольными щелями во всю высоту.
- **`stage_1_var_6` (Dual Peak Ridge)**:
  - Референс: широкий хребет с двумя сглаженными вершинами и седловиной.
  - 3D Pass: две вершины (y=10 и y=9) с понижением-седловиной (y=5) и асимметричными боковыми отрогами.

### 2. Прогрессия разрушения (Stages 2–5)
- **Stage 2 (Big Chunks)**: крупный сколотый массив (~50% массы валуна) с чёткими плоскими поверхностями сколов (`stone_primary`) и обломками у основания.
- **Stage 3 (Medium Chunks)**: компактные гранёные блоки (~25% массы), естественная группировка 2–3 каменных частей.
- **Stage 4 (Small Chunks)**: разрозненные группы из 3 отдельных камней с надёжным плоским контактом с землёй (`y=0`).
- **Stage 5 (Debris)**: россыпь мелких камней и гальки (33–38 вокселей, 438–472 треугольников), плоский силуэт высотой 2–3 вокселя.

### 3. Материальная читаемость и свет
- Верхние грани ловят свет (`stone_light`), формируя объём при взгляде сверху/в изометрии.
- Расщелины и поднутрения затемнены (`stone_dark`), создавая визуальную глубину и рельефность.
- Мох (`stone_moss`) ограничен 3–5% видимых поверхностей и локализован только в глубоких укрытых нишах, не образуя однородных ковров.

## Notes for External Reviewer
- Review package содержит:
  - `review/reference_vs_3d_comparison.png` — сопоставление всей линейки с утверждённым концептом;
  - `review/stage_1_comparison.png` — увеличенное сравнение 6 концептов Stage 1 с 3D-моделями;
  - `review/contact_sheet.png` — общий рендер всех 17 моделей;
  - 4 ракурса (iso, front, side, top) и `metrics.json` для каждого варианта.
- Все полигоны (438–2295 tris) укладываются в бюджет 5000 tris.
- Все материалы (до 4) укладываются в бюджет 4 materials.
- Все GLB экспортированы с единым мешем на материал и удалёнными внутренними гранями.
