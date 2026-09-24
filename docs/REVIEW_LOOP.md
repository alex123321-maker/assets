# Autonomous PR Review Loop

Этот репозиторий использует тот же принцип автономного review loop, что и основной Cube Siege, но с отдельными runtime state и service identifiers.

## Основной цикл

```text
Issue
  ↓
Gemini / Antigravity создаёт task branch
  ↓
asset source + build + validation + review media
  ↓
PR создаётся через create_pr.py
  ↓
branch ↔ GUI conversation сохраняется
  ↓
watcher отслеживает внешнее review
  ↓
REQUEST_CHANGES / NOT READY → сообщение в тот же чат Antigravity
  ↓
Gemini исправляет, проверяет, commit + push
  ↓
повторное внешнее review
```

## Создание PR

Штатный и обязательный способ:

```bash
python tools/review_loop/create_pr.py -- --title "..." --body "..."
```

Можно явно передать conversation id:

```bash
python tools/review_loop/create_pr.py \
  --conversation-id <id> -- \
  --title "..." --body "..."
```

Прямой `gh pr create` запрещён для agent workflow, потому что PR может оказаться без гарантированной связи с GUI conversation.

## Что делает wrapper

`tools/review_loop/create_pr.py`:

1. запрещает открывать PR из `main/master/develop`;
2. получает текущую branch;
3. получает текущий Antigravity conversation id;
4. сохраняет branch ↔ conversation до обращения к GitHub;
5. проверяет/запускает watcher;
6. создаёт либо находит PR текущей branch;
7. регистрирует PR в `.review_loop/state.json`.

## Antigravity hooks

`.agents/hooks.json` дополнительно вызывает:

```bash
python tools/review_loop/register.py --from-hook
```

после tool use и при завершении сессии. Это страховка для сохранения `conversationId` и автоматического сопоставления ветки с PR.

## Watcher

Основные команды:

```bash
python tools/review_loop/install.py install
python tools/review_loop/install.py ensure
python tools/review_loop/install.py status
python tools/review_loop/install.py start
python tools/review_loop/install.py stop
python tools/review_loop/install.py uninstall
```

Предпочтительный режим — Antigravity sidecar с id:

```text
asset-factory-review-loop
```

Fallback identifiers:
- Windows task: `AssetFactoryReviewLoopWatcher`
- Linux user service: `asset-factory-review-watcher.service`

Они намеренно отличаются от Cube Siege, поэтому оба репозитория могут иметь собственные watchers.

## Ручная регистрация

Если PR уже существует:

```bash
python tools/review_loop/register.py --conversation-id <id>
```

Дополнительные команды:

```bash
python tools/review_loop/register.py --list
python tools/review_loop/register.py --allow-user <github-login>
python tools/review_loop/register.py --unregister <pr_number>
python tools/review_loop/register.py --reactivate <pr_number>
```

## Runtime state

Локально создаётся:

```text
.review_loop/
├── state.json
├── state.lock
├── watcher.log
├── hook.log
├── watcher.pid
└── antigravity_sidecar.enabled
```

Каталог игнорируется Git.

## Поведение при review fixes

Автоматически возобновлённый Gemini / Antigravity:
- читает Issue, текущий PR, текущий head и актуальное review;
- исправляет только валидные замечания в scope;
- не додумывает художественные/gameplay решения;
- при настоящей неопределённости сообщает `DESIGN DECISION REQUIRED`;
- не публикует reviews или статусные PR comments; после push публикует актуальные визуальные вложения по [PR_VISUAL_MEDIA.md](PR_VISUAL_MEDIA.md);
- не merge PR;
- после исправления запускает требуемые asset validation/build checks;
- commit + push является сигналом watcher, что исправления готовы к повторному review.

## Проверка

Review loop покрыт unit tests:

```bash
python -m unittest discover -s tests/unit -p "test_review_loop.py"
```


## Isolated watcher runtime

To keep asset PRs free of watcher/policy changes, run the watcher from a separate
checkout and set `ASSET_REVIEW_REPO_ROOT` to the asset working repository. The
watcher loads code and `docs/PR_VISUAL_MEDIA.md` from its own checkout; GitHub
commands, feedback files, locks, PID and state remain under the target asset
repository. The sidecar installer preserves this separation in its manifest.
Install from the infrastructure checkout with the environment variable set, then
restart the Asset Factory sidecar. Keep that infrastructure checkout available.
No merge or cherry-pick into the asset branch is required.
