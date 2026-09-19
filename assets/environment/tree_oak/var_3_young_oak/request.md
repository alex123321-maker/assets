# Request: Young Oak (`var_3_young_oak`)

## Role in Family
- Slot: 3
- Name: Young Oak
- Description: Молодое дерево заметно меньшего размера (~2.4м, ~0.6x от взрослого стандарта).

## Art Direction & Integration Requirements
- **Integration slot**: `ResourceTree.tree_variation = 3` in `alex123321-maker/Cube-Siege`.
- **Silhouette**: Трёхмерная асимметричная воксельная форма; ствол и крупные массы кроны читаются с игровой камеры.
- **Pivot/Origin**: `bottom_center` ствола (y=0 плоский контакт с землей).
- **Voxel Density**: 0.15 м / воксель (согласовано с `destructible_rock`).
- **Shared Palette**:
  - `wood_bark` (`W`): тёмная кора дуба (#4a2f1b), roughness 0.92, metallic 0.0;
  - `foliage_base` (`D`): глубокая насыщенная лесная листва (#3b6b22), roughness 0.88, metallic 0.0;
  - `foliage_accent` (`L`): тёплый золотисто-зелёный акцент для верхних террас и освещённых шапок (#5e932b), roughness 0.82, metallic 0.0.
- **Occlusion**: Компактная область кроны для runtime camera-occlusion fade; без одиночных летающих вокселей.
