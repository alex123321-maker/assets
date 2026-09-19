# Request: Shrub / Bush Oak (`var_4_shrub_oak`)

## Role in Family
- Slot: 4
- Name: Shrub / Bush Oak
- Description: Низкий кустарниковый дуб (~1.35м) для горных и переходных зон.

## Art Direction & Integration Requirements
- **Integration slot**: `ResourceTree.tree_variation = 4` in `alex123321-maker/Cube-Siege`.
- **Silhouette**: Трёхмерная асимметричная воксельная форма; ствол и крупные массы кроны читаются с игровой камеры.
- **Pivot/Origin**: `bottom_center` ствола (y=0 плоский контакт с землей).
- **Voxel Density**: 0.15 м / воксель (согласовано с `destructible_rock`).
- **Shared Palette**:
  - `wood_bark` (`W`): тёмная кора дуба (#42291a);
  - `foliage_base` (`D`): глубокая насыщенная лесная листва (#1f5226);
  - `foliage_accent` (`L`): тёплый золотисто-зелёный акцент для верхних террас и освещённых шапок (#42852e).
- **Occlusion**: Компактная область кроны для runtime camera-occlusion fade; без одиночных летающих вокселей.
