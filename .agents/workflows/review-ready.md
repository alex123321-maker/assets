# /review-ready

Перед созданием PR для ассета:

1. **Issue / Request** — перечитать актуальные требования и approved references.
2. **Source audit** — canonical source сохранён и воспроизводим.
3. **Validation** — запустить `python tools/validate_asset.py <asset-package>`.
4. **Build** — выполнить требуемую Blender/build команду.
5. **Review media** — проверить обязательные виды/анимации/VFX previews.
6. **Metrics** — проверить бюджеты из manifest.
7. **Visual self-review** — silhouette, materials, voxel density, ground contact, анимация/VFX по необходимости.
8. **Diff audit** — исключить посторонние изменения и generated garbage.
9. **PR summary** — подготовить `Closes #N`, Acceptance Criteria, verification и limitations.
10. **Create PR** — только:
   ```bash
   python tools/review_loop/create_pr.py -- <аргументы gh pr create>
   ```

11. **Visual attachments** — после создания PR загрузи references и review PNG через `gh pr comment --attach` по `docs/PR_VISUAL_MEDIA.md`; укажи полный HEAD SHA, проверь опубликованные вложения и сохрани URL комментария. Повторяй после push исправлений.
