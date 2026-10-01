# Issue #52 — ImageGen HUD Art Source

## Purpose

This package stores the immutable ImageGen source art and deterministic technical exports for the Cube Siege HUD. Each runtime icon is traced to one transparent RGBA master under \`source/imagegen/masters\`; export code may crop transparent bounds, uniformly fit artwork into a padded square, and resize it. It must not draw, replace, vectorize, or otherwise synthesize icon artwork.

## Runtime catalog: 23 unique icons

- Resources (4): \`resource_wood\`, \`resource_stone\`, \`resource_iron\`, \`resource_magic_stone\`.
- Global HUD (3): \`global_day\`, \`global_night\`, \`global_settings\`.
- Build (1): \`global_build\`.
- Warrior (5): \`warrior_sword_attack\`, \`warrior_cleave\`, \`warrior_dash\`, \`warrior_parry\`, \`warrior_duel\`.
- Archer (5): \`archer_shot\`, \`archer_piercing_shot\`, \`archer_roll\`, \`archer_decoy\`, \`archer_eagle_eye\`.
- Engineer (5): \`engineer_hammer\`, \`engineer_turret\`, \`engineer_dash\`, \`engineer_mine\`, \`engineer_tactical_nuke\`.

Ability labels follow the game contract: Archer F is Eagle Eye, Engineer F is Tactical Nuke, and Engineer Q communicates whether the remote mine can be placed or detonated.

## Exports

- Transparent PNG icons at 256, 128, 64 and 32 px, all derived from the immutable masters.
- Action-slot frames, cooldown and keycap art, panel frames, progress bars, atlas and 9-patch metadata. These are technical UI components, not replacement icon art.
- Contact, 64 px and 32 px readability sheets, and class/component layouts. These layouts show generated assets and are not engine captures.
- Per-master ImageGen prompts, operation/output lineage, hashes and reference provenance in \`source/imagegen/prompts.json\`.

SVG icon output and procedural icon builders are not part of this package's production pipeline. The historical HUD reference in \`references/\` is recorded as a candidate reference, not as a new style approval. Image generation used Codex's built-in ImageGen tool; it was not sent through a Godot MCP bridge.

\n