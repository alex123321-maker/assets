# Cube Siege Asset Factory

Отдельный репозиторий для агентского производства игровых ассетов Cube Siege.

## Цель

Пользователь задаёт художественное и игровое ТЗ, **Gemini / Antigravity** выполняет производство ассета, Blender используется как детерминированный 3D-инструмент, а Pull Request служит единицей внешнего ревью.

Основной цикл:

```text
Issue / request
    ↓
references
    ↓
Gemini / Antigravity
    ↓
source asset
    ↓
build + validate + preview
    ↓
self-review
    ↓
Pull Request
    ↓
ChatGPT review
    ↓
fixes / re-review
    ↓
accepted asset
```

## Поддерживаемые типы ассетов

### `voxel_static`
Камни, деревья, руда, кусты, здания, стены, оружие, простые пропсы.

Канонический источник — дискретная 3D-воксельная сетка, которую удобно читать и редактировать слоями. Blender собирает из неё один оптимизированный mesh, а не тысячи отдельных кубов.

### `voxel_rigged`
Блочная основа существа или персонажа + последующий rig/animation этап в Blender.

### `blender_unique`
Герои, сложные монстры и уникальные объекты, для которых процедурная сетка ограничивает качество. Канонический источник — `.blend`.

### `vfx`
Исходники и референсы визуальных эффектов. Финальный runtime-VFX может жить в игровом репозитории, но визуальные концепты, текстуры, meshes и review media могут производиться здесь.

## Структура пакета ассета

```text
assets/<category>/<asset_name>/
├── request.md          # художественное/игровое ТЗ
├── manifest.json       # машинно-читаемый контракт
├── references/         # утверждённые изображения и визуальные ориентиры
├── source/             # layers / .blend / исходные текстуры
├── output/             # экспортируемые GLB/PNG и т.п.
└── review/             # рендеры, видео, metrics.json, review.md
```

## Быстрый старт

1. Создать Issue по шаблону Asset Request.
2. Создать ветку `asset/<issue>-<slug>`.
3. Скопировать `assets/_template/` в новый пакет.
4. Заполнить `request.md` и `manifest.json`.
5. Для воксельного ассета создать `source/voxels.json`.
6. Проверить:
   ```bash
   python tools/validate_asset.py assets/<category>/<asset_name>
   ```
7. Собрать через Blender:
   ```bash
   blender --background --python tools/blender/build_voxel_asset.py -- \
     --asset assets/<category>/<asset_name>
   ```
8. Сгенерировать review renders и заполнить `review/review.md`.
9. Открыть Pull Request.

Подробности: [docs/PIPELINE.md](docs/PIPELINE.md).

## Главный принцип

AI принимает художественные решения, но **геометрические операции должны быть воспроизводимыми**.

Для повторяемых блочных ассетов Gemini редактирует понятное представление формы (слои/воксели/параметры), а код детерминированно превращает его в оптимизированный mesh. Для уникальных персонажей Gemini работает непосредственно через Blender, но всё равно обязан оставлять исходник, preview и проверяемый экспорт.
