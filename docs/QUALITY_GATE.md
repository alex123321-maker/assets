# Build evidence and visual review

Новый gate применяется к новым пакетам. Старые ассеты остаются без изменений и явно
отмечаются как legacy, а не автоматически прошедшие новые проверки. Для намеренного
перевода существующего пакета используется init. Не мигрируй всё семейство попутно.

## Использование

```bash
python tools/new_asset.py environment my_prop
# new_asset создаёт quality.json с незаполненными целями/командами.
# Для пакета, созданного другим authoring script:
python tools/quality_gate.py init assets/environment/my_prop
```

Редактируй quality.json: все пути относительно корня репозитория; inputs — файлы или
каталоги канонического source и всех build dependencies. Не включай в inputs output/review.
Для семейства можно указать общие зависимости в каждом пакете; семейный build допустим
как команда, но каждый новый manifest требует собственный quality.json.

commands — последовательность массивов аргументов, без shell-перенаправлений.
Blender Python commands требуют `--python-exit-code 1` до `--python`/`--python-expr`: иначе
Blender может завершиться с кодом 0 после исключения Python и оставить старые outputs.
Если Blender запускается внутри Python wrapper, тот тоже обязан передать этот флаг. Например:

```json
[["blender", "--background", "--factory-startup", "--python-exit-code", "1", "--python", "tools/blender/build_voxel_asset.py", "--", "--asset", "assets/environment/my_prop"]]
```

Перед этим авторь source. Build не должен менять входные файлы, request или references.
Не добавляй authoring, перезаписывающий source, в build recipe. Подключи генерацию
comparison/gameplay media отдельными командами и перечисли их зависимости.
Для UI/rig/VFX замени voxel starter recipe/пути на реальные инструменты и артефакты.
Для библиотеки с внешними зависимостями явно перечисли shared inputs внутри репозитория.

artifacts — output и точные пути review PNG/metrics. Все outputs и required_views из
manifest должны входить в снимок, иначе проверка отклоняет неполную поставку. Не включай весь review/:
evidence.json и visual_review.json не являются результатами сборки и не входят в снимок.
Проверяются декодирование PNG/JPEG/WebP и количество треугольников/материалов GLB
относительно manifest, а также согласованность triangle metrics. Это не полный glTF validator.

references: path, sha256, provenance (откуда получено), status candidate/approved,
approval (ссылка на уже существующее решение, только для approved). init сохраняет hash,
но не объявляет изображения утверждёнными. Если references лежат в общей папке семейства,
добавь их явно. При осознанной смене референса обнови hash и ссылку на решение.
При ТЗ без референса заполни reference_free_reason; не создавай фиктивный approved reference.

criteria: id, конкретный target, evidence (пути к необходимым изображениям).
Пример цели: «широкая низкая крона; две видимые развилки под листвой в iso;
нет одинаковых круглых масс». Не используй «красиво / production ready» как критерий.
require_engine_review включается, если это требует Issue; иначе ограничение проверки в движке
должно быть явно раскрыто. Не ослабляй требования Issue ради зелёного gate.

```bash
python tools/quality_gate.py build assets/environment/my_prop
python tools/quality_gate.py check assets/environment/my_prop
python tools/quality_gate.py verify-clean assets/environment/my_prop
```

build запускает команды и только после их успеха пишет review/evidence.json с SHA-256
входов и результатов (у текстовых файлов CRLF приводится к LF для Windows/Linux Git;
бинарные файлы сравниваются побайтово). Source из manifest и Python entrypoints
добавляются автоматически; imported helpers/resources нужно перечислить явно.
Неудачная сборка удаляет старую квитанцию. При изменении файлов
check сообщает STALE. Это контроль актуальности, а не криптографическая аттестация
честности исполнителя и не доказательство того, что произвольный recipe действительно
перерендерил все файлы. `verify-clean` копирует только declared inputs в временную папку и
запускает recipe без старых outputs; незаявленные зависимости и no-op recipe приводят к ошибке.
Команда не меняет рабочий пакет. Она проверяет состав outputs и экспортные измерения,
GLB/обычные текстовые файлы — по hash, изображения — по декодированным RGBA с допуском
2/255 на канал и средним отклонением не более 0.001/255 для редкого округления EEVEE.
Более крупные различия, включая равномерный сдвиг цвета даже на 1/255, отклоняются. Receipt сравнения
проверяется отдельно (его image hashes меняются и при допустимом округлении).
Побайтовые различия и максимальные отклонения каналов перечисляются в отчёте.
Это не художественное одобрение и не гарантия межплатформенной идентичности. CI здесь не запускает Blender.

Сборка, изменившая или создавшая `review.md`/`visual_review.json`, отклоняется; исходные
review-файлы восстанавливаются. Даже ошибка до запуска recipe удаляет старую квитанцию.
Старый visual review не получает новый digest автоматически.

Для сравнения в идентичных условиях укажи `comparisons: ["assets/.../review/comparison.json"]`.
Receipt содержит source/image hashes и фактические настройки каждого рендера. Источники
должны быть в inputs, receipt и оба PNG — в artifacts. Gate отклоняет разные камеры,
свет, масштаб, color management, размеры и подменённые файлы. Подписи на композите нейтральны.
Это контроль согласованности trusted renderer, а не защита от намеренно поддельного receipt.

После просмотра изображений заполни review/visual_review.json:
reviewer, evidence_digest текущего снимка, inspected_images, criteria (pass/fail/not_reviewed
и конкретное observation), gameplay (checked/mockup_only/not_checked, evidence, notes),
known_deviations, feedback_resolution. Нельзя просто перенести digest на старый текст:
пересмотри затронутые изображения. Build никогда не обновляет существующий visual review.

```bash
python tools/quality_gate.py check assets/environment/my_prop --require-review
python tools/quality_gate.py check-all
```

require-review проверяет наличие и актуальность записанных наблюдений, а не их истинность.
Независимый art verdict остаётся обязанностью внешнего reviewer. Не скрывай неудавшийся
критерий; исправь его или зафиксируй решение пользователя об изменении требований.

## Пакет для браузерного ChatGPT

Сначала commit source, quality.json, outputs, evidence.json и visual_review.json.
Затем создай локальный Markdown с ссылками, зафиксированными на SHA:

```bash
python tools/quality_gate.py packet assets/environment/my_prop --repository alex123321-maker/assets --revision HEAD --output .local/my_prop-review.md
```

Для раннего ревью с честными fail/not_reviewed добавь `--draft`. Пакет получит заголовок
`DRAFT — NOT ACCEPTED`, статусы каждого критерия и engine status. Он по-прежнему требует
свежую сборку, актуальный digest и commit-проверку; наблюдения для pass/fail обязательны.
Обычный packet, `check --require-review` и CI остаются строгими. Не меняй fail на pass ради отправки PR.

Команда проверяет, что содержимое рабочих evidence совпадает с указанным commit
(с той же нормализацией CRLF/LF).
Она ничего не публикует. После push вставь содержимое файла в описание PR или передай
его браузерному reviewer. В приватном репозитории reviewer должен иметь доступ;
если изображения не открываются, он сообщает об этом и не выдаёт визуальный вердикт.
После следующего commit с изменениями пересоздай packet.

CI запускает check-all --base-ref <PR base SHA>: новые manifests требуют quality.json,
старые quality contracts нельзя молча удалить. Пакеты без контракта, существовавшие
на base SHA, не заставляют переделывать уже принятые ассеты. Изменение declared shared
dependency делает evidence использующих её пакетов устаревшим — их нужно пересобрать.
