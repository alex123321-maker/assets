# Request: HUD Visual Kit — Icons, Frames, and Action-Slot Art

## Context & Purpose

This asset package provides the complete visual UI kit for Cube Siege (Isometric Action-Survival).
The kit replaces placeholder emojis and primitive UI boxes in the runtime game with high-definition, cohesive, production-ready graphical assets matching the approved visual reference (`references/hud_concept_reference.jpg`).

## Required Scope

### 1. Resources (4 icons)
- **Wood** (`resource_wood`): Stack of chopped lumber logs with growth rings and bark texture.
- **Stone** (`resource_stone`): Chiseled granite block with angular facets and mineral sheen.
- **Iron** (`resource_iron`): Solid forged iron ingot with metallic specular highlights and clean bevels.
- **Magic Stone** (`resource_magic_stone`): Glowing purple/cyan crystal cluster radiating magical energy.

### 2. Global HUD (4 icons)
- **Day** (`global_day`): Radiant golden solar disc with stylized angular rays.
- **Night** (`global_night`): Glowing cyan crescent moon with star glints.
- **Settings** (`global_settings`): Precision mechanical cog with beveled teeth.
- **Build** (`global_build`): Crossed builder's hammer and draftsman square / architect hammer.

### 3. Warrior Abilities (5 icons)
- **LMB Sword Attack** (`warrior_sword_attack`): Steel blade delivering a swift cutting slash.
- **RMB Cleave** (`warrior_cleave`): Wide fiery circular sweep / whirlwind blade arc.
- **Space Dash** (`warrior_dash`): Forward boots with dynamic velocity streaks.
- **Q Parry** (`warrior_parry`): Deflecting shield and crossed blade with impact spark.
- **F Duel** (`warrior_duel`): Crossed swords within a crowned battle crest and blazing aura.

### 4. Archer Abilities (5 icons)
- **LMB Shot** (`archer_shot`): Elegant composite bow nocked with loose flight arrow.
- **RMB Piercing Shot** (`archer_piercing_shot`): Triple luminous cyan arrows punching through energy rings.
- **Space Roll** (`archer_roll`): Acrobatic evasive tumble swirl with wind trails.
- **Q Decoy** (`archer_decoy`): Translucent holographic shadow clone archer.
- **F Sniper** (`archer_sniper`): High-precision target reticle locked onto lethal projectile path.

### 5. Engineer Abilities (5 icons)
- **LMB Hammer** (`engineer_hammer`): Industrial war-mallet striking with electric/kinetic sparks.
- **RMB Turret** (`engineer_turret`): Automated tripod sentry gun pod with twin barrels.
- **Space Dash** (`engineer_dash`): Twin rocket thruster burst with flame exhaust cones.
- **Q Mine** (`engineer_mine`): Spiked proximity landmine with hazard stripes and warning LEDs.
- **F Overclock** (`engineer_overclock`): Overcharged lightning gears surging through a steam gauge.

### 6. Auxiliary & HUD Elements (4 icons)
- **Skull Wave** (`hud_skull_wave`): Menacing combat skull marker for wave & boss indicators.
- **Health Cross** (`hud_health_cross`): Radiant green vitality cross for healing & health.
- **Armor Shield** (`hud_armor_shield`): Heavy fortified kite shield for armor & defense.
- **Target Range** (`hud_target_range`): Concentric bulls-eye with range indicators.

### 7. Reusable Frames & UI Components
- Action slot frames in 5 states: `normal`, `hover`, `pressed`/`selected`, `disabled`, `cooldown`.
- Cooldown overlay & radial mask reference.
- Keycap frames and pre-rendered key badges (`LMB`, `RMB`, `SPACE`, `Q`, `W`, `E`, `R`, `F`, `TAB`).
- Compact top-center Day/Night header frame.
- Wave progress bar (background frame + fill).
- Floating overhead player/enemy health bar (frame + full/danger fills).
- Resource row pill container frame.
- Tooltip popup frame.

## Visual Language & Style
- Dark charcoal/navy palettes (`#0D131A`, `#151F2C`, `#1D2A3A`) providing high contrast against voxel environments.
- Vibrant cold cyan/blue accents (`#2CD8FF`, `#00A3E0`) for active abilities and night themes.
- Warm fiery red/orange accents (`#FF3B30`, `#FF5722`, `#FF9800`) for danger, HP, and warrior cleave.
- Radiant golden/amber tones (`#F5A623`, `#FFD23F`) for daylight, resources, and masteries.
- Strict silhouette clarity: icons must remain instantly recognizable at 32px and 64px.
- Zero emojis; cohesive vector and pixel-rendered game assets.

## Delivery Requirements
- Vector SVGs and high-resolution master PNGs (256x256).
- Scaled game-ready icon exports (128x128, 64x64, 32x32) with alpha transparency.
- 9-patch slice metadata in JSON for Godot `NinePatchRect` / `TextureRect`.
- Packed spritesheet atlas (`output/atlas/hud_atlas.png`) with JSON coordinate map.
- Review contact sheets, 64px & 32px readability sheets, class HUD strips, Day/Night mockup, Resource bar mockup, and full assembled gameplay mockup.
