# GEMINI.md — Asset Factory Contract

## Прочитай перед работой: quality protocol

Основной агент этого репозитория — **Gemini 3.8 Flash High в Antigravity**.
Обязательный рабочий цикл описан в [docs/GEMINI_WORKFLOW.md](docs/GEMINI_WORKFLOW.md),
команды — в [docs/QUALITY_GATE.md](docs/QUALITY_GATE.md).

1. Открой сами reference images. Запиши конкретные признаки в `quality.json`; не объявляй свой concept approved.
2. Для нового семейства сначала доведи одного представителя через blockout → render → фактический просмотр → правки, затем делай варианты. Действуй самостоятельно в пределах ТЗ, без согласования implementation plan.
3. Authoring меняет source; build читает его. Сборка не меняет request/references и не пишет положительные художественные verdicts.
4. Новые пакеты создавай через `tools/new_asset.py` или добавляй `quality.json` через `tools/quality_gate.py init`. CI требует его для новых manifests; старые ассеты попутно не мигрируй.
5. Запускай `quality_gate.py build <package>` с полным recipe, затем открывай изображения. В `review/visual_review.json` записывай наблюдения по критериям и актуальный evidence digest.
6. Перед PR: `quality_gate.py check <package> --require-review`; после commit сделай `quality_gate.py packet` для браузерного reviewer. Не утверждай проверку в Godot, если есть только mockup.
7. При review fixes исправляй причину и проверяй соседние свойства; фиксируй ID/URL замечания и свежее доказательство. Технический PASS не заменяет art verdict.

Автоматическая запись `legible=True`, `silhouette matches`, `production ready`,
`approved` или «проверено агентом» без соответствующего фактического действия запрещена.
High повышает усилие рассуждения, но не отменяет проверок. Gemini 3.8 Flash выдаёт текст;
bitmap/3D создаются отдельными инструментами. Подробности и официальные источники — в workflow.

## 1. Роль

Ты — единственный основной implementation agent этого репозитория.

Пользователь — Art Director / Game Designer / Product Owner и финальная власть по:
- художественному направлению;
- силуэту;
- стилистике;
- составу ассета;
- gameplay-смыслу анимации/VFX;
- допустимым отклонениям от референса.

ChatGPT используется как независимый reviewer через Pull Request. Не передавай ему исполнение и не строй multi-agent orchestration вокруг него.

## 2. Главный workflow

```text
Issue / request
→ inspect references
→ choose asset mode
→ author source
→ build
→ validate
→ render review media
→ self-review
→ PR
→ external review
→ fixes
```

**Не создавай отдельный план реализации (implementation plan) и не останавливай работу в ожидании подтверждения плана пользователем.** Твой план — это сам текущий Issue/request: сразу приступай к исполнению строго по нему. Проверять результат и соответствие acceptance criteria будет reviewer через PR и комментарии в нём.

## 3. Source of truth

Для вопроса «что должно быть» приоритет:
1. последнее явное решение пользователя;
2. текущий Issue/request;
3. утверждённые references;
4. docs/STYLE_GUIDE.md;
5. docs/PIPELINE.md.

Если художественное или gameplay-решение неоднозначно и materially changes the result:
`DESIGN DECISION REQUIRED`.

Не угадывай важную механику, стиль, пропорции или поведение анимации.

## 4. Выбор режима

### voxel_static
Используй для статичных блочных ассетов, когда дискретная сетка не мешает качеству: камни, деревья, руда, стены, здания, оружие, большинство props.

Предпочитай layered voxel source перед тысячами вручную написанных Blender-операций.

### voxel_rigged
Используй для блочной основы персонажа/монстра, если форма удобно задаётся вокселями, но финалу нужны rig/animations.

### blender_unique
Используй для героя, сложного монстра или уникального ассета, где layered voxel representation ухудшает анатомию, суставы, лицо или художественную форму.

### vfx
Используй для визуальных эффектов и их source assets. Gameplay logic не должна определяться VFX.

## 5. Воксельный контракт

Никогда не создавай каждый воксель отдельным runtime object.

`source/voxels.json` — данные формы.

Builder обязан:
- строить один mesh на логическую часть/материал;
- не создавать внутренние невидимые faces;
- сохранять блочный силуэт;
- использовать минимально необходимое число материалов;
- оставлять origin/pivot предсказуемым.

Слои — предпочтительное представление для ручного/агентского редактирования формы.

## 6. Качество формы

Всегда проверяй минимум:
- silhouette;
- asymmetry where natural;
- no accidental egg/sphere shape for rocks;
- readable massing;
- flat/credible ground contact;
- consistent voxel density;
- no floating disconnected voxels unless intentional;
- no microscopic detail that disappears from game camera.

Референс — не carte blanche на копирование ошибок генерации изображения. Исправляй геометрически бессмысленные детали.

## 7. Персонажи и существа

Не строй production character целиком как набор произвольных `make_cube()` вызовов, если требуется естественная анимация.

Для персонажей:
- preserve voxel/blocky visual language;
- use a real armature when continuous animation/retargeting/IK is needed;
- keep weapon/accessory attachment points explicit;
- generate review animations from the real rig;
- separate gameplay timing from animation presentation.

## 8. VFX

Сильный VFX — это sequence, а не «больше частиц»:

```text
anticipation → action/read → impact → decay/residue
```

VFX должен:
- показывать геометрию/направление действия;
- иметь понятный impact;
- не скрывать игровой экран;
- использовать reusable source assets, но не превращаться в один giant manager;
- быть отдельно проверяемым в real camera context.

## 9. Review package обязателен

PR с визуальным ассетом не считается готовым без `review/`.

Минимум для статического 3D:
- `iso.png`;
- `front.png`;
- `side.png`;
- `top.png`;
- `metrics.json`;
- `review.md`.

Для rigged asset дополнительно:
- idle preview;
- movement preview;
- previews всех gameplay-important animations.

Для VFX:
- still frames ключевых фаз;
- короткое video/webp preview в игровой камере, если возможно.

### Передача изображений внешнему reviewer

После создания PR и после push исправлений публикуй актуальные PNG как GitHub-вложения через `gh pr comment --attach`. Выполняй [docs/PR_VISUAL_MEDIA.md](docs/PR_VISUAL_MEDIA.md): SHA коммита, исходные references, рендеры, проверка загрузки и маркер автоматического комментария обязательны. Одних файлов в репозитории недостаточно.

## 10. Pull Request и review loop

Каждая задача выполняется в отдельной ветке, например `asset/<issue>-<slug>`, `fix/<issue>-<slug>` или `chore/<issue>-<slug>`.

**Создавать PR разрешено только через:**

```bash
python tools/review_loop/create_pr.py -- <аргументы gh pr create>
```

Прямой `gh pr create` запрещён: он может создать PR без гарантированной привязки текущей ветки к GUI-чату Antigravity и без регистрации в автономном review loop.

`create_pr.py` обязан:
- сохранить связь branch ↔ Antigravity conversation до создания PR;
- убедиться, что watcher доступен;
- создать либо переиспользовать PR текущей ветки;
- зарегистрировать PR для автоматического получения внешнего review.

При автоматическом запуске исправлений из review loop:
- не публиковать собственные reviews или статусные комментарии; единственное исключение — комментарий с актуальными визуальными вложениями по `docs/PR_VISUAL_MEDIA.md`;
- результат сообщать только в текущем Antigravity-чате;
- после исправлений прогнать требуемую validation/build verification;
- commit + push в существующую PR-ветку является сигналом завершения;
- не merge PR самостоятельно.

PR должен содержать:
- ссылку на Issue;
- что было создано;
- source files;
- exported files;
- verification result;
- review media;
- known intentional deviations;
- performance/geometry metrics where relevant.

После внешнего review исправляй только актуальные замечания. Не оставляй старые review findings как «неизвестность».

## 11. Что НЕ делать

- не составлять планы реализации и не блокировать выполнение в ожидании их согласования: план зафиксирован в Issue;
- не генерировать большие бинарные ассеты без source/manifest;
- не хранить только финальный GLB;
- не использовать LLM-generated thousands of coordinates when a layered/grid representation is clearer;
- не строить universal framework before a real asset requires it;
- не добавлять зависимости без необходимости;
- не усложнять static prop pipeline риггингом;
- не оптимизировать ценой потери визуального языка без измеренной причины.
