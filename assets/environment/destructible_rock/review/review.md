# Family Self Review: Destructible Rock (17 Variants, 5 Stages)

## Acceptance Criteria Checklist

- [x] **Ровно 17 вариантов**: 6 (Stage 1) / 3 (Stage 2) / 3 (Stage 3) / 2 (Stage 4) / 3 (Stage 5).
- [x] **Canonical Source**: Каждый вариант имеет полностью воспроизводимый `source/voxels.json` в layered voxel representation.
- [x] **Repository Validation**: Все варианты проходят `tools/validate_asset.py` и общий `tools/validate_all.py`.
- [x] **Blender Pipeline**: Все варианты успешно собираются через скрипты сборки (`build_voxel_asset.py`, `build_family.py`) на Blender 5.2.1 LTS.
- [x] **GLB Export**: Каждый вариант экспортирует валидный `output/model.glb` для Godot с единым мешем на материал.
- [x] **No Individual Cube Objects**: Ни один вариант не использует отдельные cube nodes в рантайме.
- [x] **Internal Face Culling**: Внутренние грани между смежными занятыми вокселями полностью удалены.
- [x] **Silhouette Diversity (Stage 1)**: Все 6 вариантов Stage 1 обладают выраженно различными силуэтами (Ridge, Split Peak, Slanted Wedge, Overhanging Crag, Jagged Butte, Elongated Slab).
- [x] **Silhouette Diversity (Stages 2–5)**: Внутри каждой последующей стадии формы также визуально различимы.
- [x] **Monotonic Mass Reduction**: Объем и количество вокселей строго и последовательно уменьшаются от Stage 1 к Stage 5 (100% → ~50% → ~25% → ~12% → ~4%).
- [x] **No Spherical/Egg Shapes**: Камни имеют граненые, ступенчатые поверхности с контролируемой асимметрией.
- [x] **Ground Contact & Pivot**: Все варианты имеют плоский контакт с землей (`y=0`) и центрированный `bottom_center` origin.
- [x] **Unified Material**: Один семейный стилизованный серый камень `stone_gray` с roughness 0.92 и flat shading.
- [x] **Review Package**: Для каждого из 17 вариантов созданы ракурсы `iso.png`, `front.png`, `side.png`, `top.png` и `metrics.json`.
- [x] **Family Contact Sheet**: Сгенерирован общий обзорный контакт-лист `contact_sheet.png` со всеми 17 вариантами, сгруппированными по рядам стадий.

## Summary of Metrics

| Variant | Stage | Occupied Voxels | Triangles | Visible Faces | Grid (X x Y x Z) | World Size (m) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `stage_1_var_1` | 1 | 750 | 1476 | 738 | 16 x 12 x 16 | 2.4 x 1.8 x 2.4 |
| `stage_1_var_2` | 1 | 805 | 1444 | 722 | 16 x 12 x 16 | 2.4 x 1.8 x 2.4 |
| `stage_1_var_3` | 1 | 893 | 1412 | 706 | 16 x 12 x 16 | 2.4 x 1.8 x 2.4 |
| `stage_1_var_4` | 1 | 788 | 1452 | 726 | 16 x 12 x 16 | 2.4 x 1.8 x 2.4 |
| `stage_1_var_5` | 1 | 870 | 1704 | 852 | 16 x 12 x 16 | 2.4 x 1.8 x 2.4 |
| `stage_1_var_6` | 1 | 922 | 1472 | 736 | 18 x 11 x 15 | 2.7 x 1.65 x 2.25 |
| `stage_2_var_1` | 2 | 594 | 1056 | 528 | 14 x 9 x 14 | 2.1 x 1.35 x 2.1 |
| `stage_2_var_2` | 2 | 411 | 864 | 432 | 14 x 8 x 14 | 2.1 x 1.2 x 2.1 |
| `stage_2_var_3` | 2 | 420 | 928 | 464 | 14 x 8 x 14 | 2.1 x 1.2 x 2.1 |
| `stage_3_var_1` | 3 | 235 | 556 | 278 | 12 x 7 x 12 | 1.8 x 1.05 x 1.8 |
| `stage_3_var_2` | 3 | 212 | 548 | 274 | 12 x 6 x 12 | 1.8 x 0.9 x 1.8 |
| `stage_3_var_3` | 3 | 276 | 576 | 288 | 12 x 6 x 12 | 1.8 x 0.9 x 1.8 |
| `stage_4_var_1` | 4 | 127 | 436 | 218 | 12 x 5 x 12 | 1.8 x 0.75 x 1.8 |
| `stage_4_var_2` | 4 | 130 | 492 | 246 | 12 x 4 x 12 | 1.8 x 0.6 x 1.8 |
| `stage_5_var_1` | 5 | 36 | 228 | 114 | 10 x 3 x 10 | 1.5 x 0.45 x 1.5 |
| `stage_5_var_2` | 5 | 33 | 212 | 106 | 10 x 3 x 10 | 1.5 x 0.45 x 1.5 |
| `stage_5_var_3` | 5 | 38 | 232 | 116 | 10 x 3 x 10 | 1.5 x 0.45 x 1.5 |

## Known Intentional Deviations
None.

## Notes for External Reviewer
- Обратите внимание на `contact_sheet.png`: на нем представлены все 17 вариантов в едином пространстве с одинаковым студийным освещением и изометрической камерой.
- Все треугольники находятся в диапазоне 212–1704 при лимите 5000 на меш.
- Каждый вариант изолирован и готов к непосредственному инстанцированию в Godot 4.
