---
name: Asset Request
about: Request a new 3D / voxel / character / VFX asset
title: "[ASSET] "
labels: []
assignees: []
---

## Goal

Что нужно создать и зачем этот ассет нужен игре.

## Asset Type

- [ ] voxel_static
- [ ] voxel_rigged
- [ ] blender_unique
- [ ] vfx

## Player-facing / Visual Role

Как игрок видит и считывает этот объект.

## Shape / Silhouette

Ключевые массы, пропорции, асимметрия, обязательные элементы.

## Variants / Stages

Нужные варианты, стадии разрушения, состояния или LOD.

## Materials

Какие материалы должны визуально различаться.

## Animation / VFX

Что должно двигаться / какие эффекты нужны. Если не требуется — None.

## References

Приложить или перечислить утверждённые визуальные референсы.

Для каждого: источник, статус candidate/approved, ссылка на существующее утверждение.
Укажи соответствие crop/варианта; не требуй фиктивного one-to-one для family reference.

## Observable visual targets

4–8 признаков, по которым можно сравнить изображения: пропорции, массы, просветы,
язык граней, цветовые отношения, характер материалов. Отдельно укажи допустимые отклонения.

## Gameplay review context

Камера/масштаб на экране, персонаж для сравнения, день/ночь, фон/плотность.
Нужна ли проверка в Godot, или для этой задачи достаточно явно обозначенного mockup?

## Out of Scope

Что намеренно не входит в эту задачу.

## Open Design Decisions

Любая существенная неопределённость должна быть явно перечислена здесь. Gemini не должен додумывать её самостоятельно.

## Acceptance Criteria

- [ ] Source сохранён и воспроизводим.
- [ ] Runtime export создан.
- [ ] Review renders созданы.
- [ ] Asset соответствует silhouette/style требованиям.
- [ ] Validation проходит.
- [ ] Known deviations перечислены.
