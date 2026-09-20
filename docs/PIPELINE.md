# Asset Production Pipeline

## Актуальный quality protocol для новых пакетов

[GEMINI_WORKFLOW.md](GEMINI_WORKFLOW.md) определяет художественные итерации,
[QUALITY_GATE.md](QUALITY_GATE.md) — `quality.json`, запуск build, контроль свежести
и пакет для браузерного PR reviewer. Эти правила дополняют базовую структуру ниже.
Старые пакеты не сертифицируются новым gate автоматически и не требуют массовой миграции.
Автогенерируемые измерения идут в `review/build_report.md`; `review.md` и
`visual_review.json` не перезаписываются build. Существующий положительный текст
не переносится автоматически в новый visual review.

## 1. Единица работы

Один ассет = один self-contained package:

```text
assets/<category>/<name>/
├── request.md
├── manifest.json
├── references/
├── source/
├── output/
└── review/
```

Пакет должен быть переносимым: reviewer может понять цель, исходник, экспорт и доказательства качества, не читая историю чата.

## 2. Workflow

### Шаг 1 — Request

`request.md` фиксирует:
- что это за объект;
- где/как он используется;
- ключевой силуэт;
- допустимую детализацию;
- размеры/масштаб, если они известны;
- варианты/стадии;
- animation/VFX requirements;
- approved references;
- явно открытые design decisions.

### Шаг 2 — Manifest

`manifest.json` содержит машинно-читаемые сведения:
- asset name;
- type;
- version;
- source mode;
- expected outputs;
- review requirements;
- budgets/constraints.

### Шаг 3 — Source

#### voxel_static
Источник: `source/voxels.json`.

Представление специально рассчитано на LLM/agent editing:
- дискретные слои по Y;
- строка = ряд по Z;
- символ = material token;
- `.` = пустой voxel.

#### voxel_rigged
Воксельная форма может быть стартовой, но production source после rigging — `.blend`.

#### blender_unique
Источник: `.blend` + необходимые texture/source files.

#### vfx
Источник зависит от эффекта: meshes, textures, shader snippets, reference renders и т.п.

### Шаг 4 — Build

Для `voxel_static`:

```bash
python tools/validate_asset.py assets/environment/rock_01

blender --background \
  --python tools/blender/build_voxel_asset.py -- \
  --asset assets/environment/rock_01
```

Builder:
1. читает manifest + voxel source;
2. проверяет grid;
3. удаляет внутренние faces;
4. создаёт flat-shaded mesh;
5. создаёт один object на material token;
6. выставляет pivot в согласованную точку;
7. экспортирует GLB;
8. рендерит review views;
9. пишет metrics.json.

### Шаг 5 — Self-review

Gemini сравнивает:
- request;
- references;
- STYLE_GUIDE;
- review renders;
- metrics.

Если форма визуально не проходит — source меняется, build повторяется.

### Шаг 6 — Pull Request

PR является review package.

В PR должны находиться:
- source;
- export;
- review media;
- metrics;
- заполненный review.md.

PR description должен объяснять:
- что создано;
- как проверено;
- какие intentional deviations есть;
- какие design decisions остаются открытыми.

## 3. Воксельные ассеты

### Почему слои

Слои дают агенту визуально понятное представление формы и лучше подходят для редактирования, чем тысячи координат:

```text
Y=2
..AA...
.AAAA..
AAAAAA.
.AAAA..
```

Gemini может локально исправить силуэт слоя, не пересоздавая Blender geometry вручную.

### Координаты

- X: слева → направо внутри строки.
- Y: номер слоя снизу → вверх.
- Z: строки массива от задней части к передней.
- Origin по умолчанию: bottom-center.

### Материалы

Символы задаются в `materials`.

Пример:

```json
{
  "materials": {
    "S": {
      "name": "stone",
      "base_color": [0.45, 0.47, 0.50, 1.0],
      "roughness": 0.9,
      "metallic": 0.0
    }
  }
}
```

Один материал может использовать цветовые вариации через geometry/material pipeline позже, но baseline не должен плодить десятки материалов ради шума.

## 4. Варианты и стадии

Для ресурса с разрушением варианты могут быть независимы по стадиям.

Пример:

```text
Stage 1: A B C D E F
Stage 2: A B C
Stage 3: A B C
Stage 4: A B
Stage 5: A B C
```

При смене стадии runtime может выбрать случайную форму следующей стадии и скрыть swap через destruction VFX.

Не требуется сохранять геометрическое происхождение `A1 → A2`, если визуальный эффект разрушения делает переход убедительным.

Приоритет разнообразия обычно:
1. intact/world-visible stage;
2. final rubble/readable pickup stage;
3. промежуточные стадии.

Точное число вариантов — свойство конкретного Issue, а не правило framework.

## 5. Optimization contract

В source может быть сколько угодно voxel cells. Runtime export не должен быть набором Node/Object per voxel.

Baseline:
- internal faces culled;
- flat shading;
- one mesh object per material;
- one GLB asset;
- textures/material count kept small;
- collision is generated/implemented separately and проще visual mesh.

Слияние копланарных граней допустимо при сохранении силуэта, границ материалов, UV и нормалей.
Само число coplanar polygons не создаёт визуальную блочность. Проверяй изображение и
профиль экспорта; не вводи оптимизацию или запрет на неё вместо художественного критерия.

## 6. Персонажи

Для героя или сложного монстра layers могут использоваться для blockout, но production pipeline:

```text
reference
→ blockout
→ Blender source
→ armature
→ materials
→ animations
→ export
→ gameplay-camera review
```

Ключевые требования:
- real armature for natural animation;
- explicit weapon/attachment points;
- no gameplay timing ownership in animation;
- review every gameplay-important animation.

## 7. VFX

VFX review должен доказывать четыре фазы, если они применимы:

```text
anticipation → action/read → impact → decay/residue
```

Runtime effect может собираться уже в Cube Siege, но source visual assets и concept media могут производиться здесь.

## 8. Done

Ассет готов к внешнему review, когда:
- source reproducible;
- validation green;
- expected export exists;
- required review media exists;
- metrics within declared budgets;
- no unresolved design ambiguity hidden inside implementation;
- self-review completed.
