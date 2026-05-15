"""Манифест урока lesson.json — единственный источник истины о шагах урока.

Структура:
{
  "lesson_id": 2289261,
  "steps": [
    {"position": 1, "step_source_id": 10209173, "type": "code",        "cost": 1},
    {"position": 4, "step_source_id": 10209171, "type": "free-answer", "cost": 1,
     "instruction_type": "peer", "instruction_id": 112848,
     "is_attachments_enabled": false, "is_html_enabled": true, "manual_scoring": false},
    {"position": 5, "step_source_id": 10191888, "type": "choice",      "cost": 0}
  ]
}

Каждый шаг хранится в подпапке: {pos:02d}_{type_safe}/
  type_safe = type.replace("-", "_")  (напр. "free_answer", "fill_blanks")

Содержимое подпапки по типу:
  text        →  task.html
  free-answer →  task.html  [+ instruction.json если есть рецензирование]
  code        →  task.html + step.json + checker.py (если есть)
  dataset     →  task.html + step.json + dataset.py
  sql         →  task.html + step.json + init.sql + solve.sql + checker.py
  html        →  task.html + step.json + template.html + template.css
  остальные   →  task.html + step.json  (вопросы: choice, matching, fill-blanks,
                                          number, string, math, random-tasks, table)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MANIFEST_FILENAME = "lesson.json"


def step_folder(lesson_folder: Path, position: int, step_type: str) -> Path:
    """Подпапка шага: {pos:02d}_{type_safe}."""
    type_safe = step_type.replace("-", "_")
    return lesson_folder / f"{position:02d}_{type_safe}"


def load_manifest(lesson_folder: Path) -> dict[str, Any]:
    path = lesson_folder / MANIFEST_FILENAME
    if not path.exists():
        return {"lesson_id": None, "steps": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(lesson_folder: Path, manifest: dict[str, Any]) -> None:
    manifest = dict(manifest)
    manifest["steps"] = sorted(manifest.get("steps", []), key=lambda s: s["position"])
    path = lesson_folder / MANIFEST_FILENAME
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def upsert_step(manifest: dict[str, Any], step_entry: dict[str, Any]) -> None:
    steps: list[dict[str, Any]] = manifest.setdefault("steps", [])
    position = step_entry["position"]
    for i, existing in enumerate(steps):
        if existing["position"] == position:
            steps[i] = step_entry
            return
    steps.append(step_entry)


def get_step_entry(manifest: dict[str, Any], position: int) -> dict[str, Any] | None:
    for step in manifest.get("steps", []):
        if step["position"] == position:
            return step
    return None
