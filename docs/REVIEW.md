# External Review Contract

ChatGPT используется как независимый reviewer Pull Request, а не как implementation agent.

## Что проверять

### Для static / voxel assets
- соответствие Issue/request;
- силуэт и читаемость;
- соответствие approved references;
- согласованность voxel density;
- отсутствие случайной сферичности/симметрии;
- ground contact;
- materials/readability;
- variants/stages;
- metrics/budgets;
- воспроизводимость source → output.

### Для characters / monsters
Дополнительно:
- anatomy/proportions относительно утверждённого стиля;
- rig structure;
- deformation at joints;
- weapon/attachment placement;
- idle/movement/gameplay animations;
- clipping and foot sliding;
- gameplay-camera readability.

### Для VFX
Дополнительно:
- anticipation;
- action/read;
- impact;
- decay/residue;
- area/direction readability;
- visual noise;
- performance evidence when effect is high-volume.

## Вердикты

- `READY TO MERGE`
- `READY WITH NON-BLOCKING NOTES`
- `NOT READY`

## Findings

- `BLOCKER` — asset нельзя принимать.
- `IMPORTANT` — желательно исправить до принятия.
- `NON-BLOCKING` — улучшение можно отложить.

## Design uncertainty

Reviewer не должен придумывать художественное/gameplay решение за Product Owner.

Если review обнаружил настоящую неоднозначность дизайна:
`DESIGN DECISION REQUIRED`

До решения пользователя implementation agent не должен получать выдуманный ответ.

## Re-review

При новом PR head:
1. сравнить новый head с ранее проверенным;
2. проверить исправления прошлых blockers;
3. проверить новые regressions;
4. проверить CI текущего head;
5. обновить review только актуальными findings.
