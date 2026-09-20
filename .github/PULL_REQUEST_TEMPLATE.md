## Asset

Closes #

**Type:** `voxel_static / voxel_rigged / blender_unique / vfx / ui_kit / pipeline`

## What was created

Кратко опиши результат.

## Source

- Canonical source:
- References:
- Generator/build command:

## Runtime outputs

- Model / textures / animation / VFX outputs:

## Visual review

Для asset PR вставь Markdown от `quality_gate.py packet` после commit/push:
ссылки должны указывать на точный SHA. Для pipeline-only PR укажи N/A и проверки кода.
Не выдавай автоматически созданный текст за художественное ревью.

- Reviewed/build commit:
- Reference provenance + user approval citation (или candidate / request-only):
- Evidence digest:
- Engine check: `checked / mockup_only / not_checked`, ограничения:

| View | Artifact |
| --- | --- |
| ISO | `review/iso.png` |
| Front | `review/front.png` |
| Side | `review/side.png` |
| Top | `review/top.png` |

Для анимаций/VFX добавь соответствующие preview media.

## Verification

- [ ] `python tools/validate_asset.py <asset-package>`
- [ ] Build completed successfully.
- [ ] Required review media generated.
- [ ] `review/metrics.json` checked against budgets.
- [ ] `quality_gate.py check <asset-package> --require-review` (new/enrolled packages).
- [ ] Actual reference and result images opened; observations recorded per criterion.
- [ ] No hidden design decisions were guessed.

## Metrics

Вставь краткие ключевые числа из `review/metrics.json`.

## Known intentional deviations

Перечисли видимые отклонения и непроверенные требования. `None` допустимо только после просмотра.

## Response to prior findings

| Finding ID / URL | Root cause / fix | Current evidence | Status |
| --- | --- | --- | --- |

## Reviewer focus

Что именно стоит внимательно проверить визуально/технически.
