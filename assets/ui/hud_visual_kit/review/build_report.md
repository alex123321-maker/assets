# Build measurements: HUD visual kit

Generated measurements, not an artistic verdict.

## Metrics

```json
{
  "kit_name": "hud_visual_kit",
  "total_unique_icons": 23,
  "categories": {
    "resource": 4,
    "global_hud": 3,
    "build": 1,
    "warrior": 5,
    "archer": 5,
    "engineer": 5
  },
  "resolutions_provided": [
    256,
    128,
    64,
    32
  ],
  "total_icon_files": 92,
  "total_frame_files": 25,
  "total_bar_files": 7,
  "atlas": {
    "dimensions": "1024x1024",
    "file": "output/atlas/hud_atlas.png",
    "metadata": "output/atlas/hud_atlas.json"
  },
  "godot_integration": {
    "ninepatch_slices_file": "output/hud_slices.json",
    "slices_count": 17
  },
  "review_evidence": {
    "contact_sheet": "review/contact_sheet.png",
    "readability_64px": "review/readability_64px.png",
    "readability_32px": "review/readability_32px.png",
    "mockup_warrior_hud": "review/mockup_warrior_hud.png",
    "mockup_archer_hud": "review/mockup_archer_hud.png",
    "mockup_engineer_hud": "review/mockup_engineer_hud.png",
    "mockup_day_night_panel": "review/mockup_day_night_panel.png",
    "mockup_resource_panel": "review/mockup_resource_panel.png"
  },
  "visual_review_status": "recorded in review/visual_review.json",
  "engine_verification_status": "not_checked; see the game runtime review for Issue #52"
}
```

Validate export budgets and freshness with tools/quality_gate.py.
Visual review: not performed by this generator. See visual_review.json.
