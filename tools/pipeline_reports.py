"""Generated build facts must not overwrite authored visual reviews or requests."""
from __future__ import annotations

import json
from pathlib import Path


def initialize_text(path: Path, text: str) -> bool:
    """Initialize a design document once. Later edits must be explicit, not a build side effect."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(text)
    except FileExistsError:
        return False
    return True


def write_build_report(review_dir: Path, title: str, metrics: dict) -> None:
    """Only report supplied measurements; do not claim budgets/visual checks were performed."""
    review_dir.mkdir(parents=True, exist_ok=True)
    text = (f"# Build measurements: {title}\n\n"
            "Generated measurements, not an artistic verdict.\n\n"
            "## Metrics\n\n```json\n" + json.dumps(metrics, ensure_ascii=False, indent=2) + "\n```\n\n"
            "Validate export budgets and freshness with tools/quality_gate.py.\n"
            "Visual review: not performed by this generator. See visual_review.json.\n")
    (review_dir / "build_report.md").write_text(text, encoding="utf-8")
    initialize_text(review_dir / "review.md", "# Visual review\n\n"
                    "## Objective Build Verification\n\nSee build_report.md and evidence.json.\n\n"
                    "## Metrics\n\nSee metrics.json (or family metrics_summary.json).\n\n"
                    "## Visual observations\n\nNot reviewed. Inspect images before recording a verdict.\n")
