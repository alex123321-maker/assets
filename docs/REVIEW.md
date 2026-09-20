# External Review Contract

ChatGPT используется как независимый reviewer Pull Request, а не как implementation agent.

## Работа через браузер

1. Зафиксируй проверяемый head SHA. Открой Issue, последние решения пользователя и
   `quality.json`, затем сами референсы и изображения текущего commit. Используй
   [review packet](QUALITY_GATE.md), а не moving branch links.
2. Сначала составь собственные визуальные наблюдения, затем читай самоотчёт автора.
   Зелёный CI, описание PR, названия файлов и наличие PNG не доказывают art quality.
3. Укажи пути реально просмотренных изображений. Если browser не открыл изображение
   или доступ закрыт, запиши `ART NOT VERIFIED`; не делай вид, что просмотр состоялся.
4. Сравни силуэт, пропорции/просветы, язык поверхностей, цветовые отношения и игровую
   читаемость. Проверяй один масштаб, одинаковые ракурсы, original-size crops.
   Не требуй буквального совпадения освещения concept art с PBR render.
5. Раздельно запиши **Technical**, **Art**, **Engine**: pass / fail / not_verified.
   Engine может быть not_verified при разрешённом mockup-only scope, но это нельзя
   называть готовностью, проверенной в игре. Обязательное непроверенное требование
   блокирует общий READY. Пакет метрик и checks не оценивает красоту автоматически.
6. Каждый finding содержит стабильный ID (например ART-01), severity, путь изображения/
   место, наблюдаемый симптом, нарушенный критерий Issue и проверяемое условие исправления.
   Не заменяй форму implementation-предписанием «добавь bevel». Не придумывай новые
   требования к утверждённому дизайну. Фиксируй расхождения, даже если все файлы на месте.
7. При re-review составь таблицу прошлых ID: resolved / still_open / superseded
   решением пользователя. Проверь регрессии и снова дай общий art verdict, если
   менялись геометрия, материал, камера или рендер. Полный новый art review не нужен
   для чистой правки metadata при неизменных image hashes; укажи границы повторной проверки.

Формат ответа: SHA → Technical/Art/Engine → inspected images → актуальные findings
с acceptance conditions → статус предыдущих findings → общий verdict из списка ниже.
Числа из источника, оценку reviewer и допущения отмечай раздельно. Отсутствие unresolved
threads не означает отсутствие художественных проблем.

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
