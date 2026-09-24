# Asset Issue-Driven Development Rule

## 1. Авторитетный жизненный цикл

```text
Issue
→ прочитать требования и утверждённые references
→ проверить DESIGN DECISION REQUIRED
→ создать task branch
→ создать/изменить source
→ build + validation
→ review renders / metrics
→ self-review
→ PR через tools/review_loop/create_pr.py
→ external review
→ fixes
→ re-review
→ merge
```

## 2. Scope

- Одна Issue задаёт границы одного изменения/семейства ассетов.
- Не менять художественный стиль, gameplay-смысл, пропорции или анимационное поведение без требования.
- Не делать opportunistic framework/refactor вне задачи.
- Если найден отдельный долг — вынести в follow-up.

## 3. Branches

Работа напрямую в `main` запрещена.

Примеры:
- `asset/<issue>-<slug>`
- `fix/<issue>-<slug>`
- `chore/<issue>-<slug>`

## 4. Pull Request

PR создаётся **только** через:

```bash
python tools/review_loop/create_pr.py -- <аргументы gh pr create>
```

Прямой `gh pr create` запрещён: wrapper обеспечивает связь branch ↔ Antigravity conversation и регистрацию PR в review loop.

PR должен содержать:
1. `Closes #N` или `Fixes #N`;
2. что создано/изменено;
3. canonical source;
4. runtime outputs;
5. validation/build evidence;
6. review media;
7. metrics;
8. checklist Acceptance Criteria;
9. known deviations/limitations.

## 5. Review loop fixes

При автоматическом возобновлении после review:
- не создавать implementation plan для подтверждения;
- сразу читать актуальный feedback и работать;
- не публиковать reviews или статусные PR comments; разрешён только комментарий с визуальными вложениями по `docs/PR_VISUAL_MEDIA.md`;
- не менять дизайн для удобства исправления;
- не merge PR;
- commit + push в существующую branch — сигнал завершения.

Если исправление требует нового художественного/gameplay решения:
`DESIGN DECISION REQUIRED`.
