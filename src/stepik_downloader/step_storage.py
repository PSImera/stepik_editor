"""Сериализация шагов: Stepik API ↔ локальные файлы.

Каждый шаг — своя подпапка {pos:02d}_{type_safe}/.
Содержимое по типу:
  text        →  task.html
  free-answer →  task.html  [+ instruction.json]
  code        →  task.html + step.json + checker.py
  dataset     →  task.html + step.json + dataset.py
  sql         →  task.html + step.json + init.sql + solve.sql + checker.py
  html        →  task.html + step.json + template.html + template.css
  остальные   →  task.html + step.json
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from .lesson_manifest import step_folder
from .step_types import (
    CODE_STEP_TYPES,
    DATASET_STEP_TYPES,
    FREE_ANSWER_STEP_TYPES,
    HTML_TASK_STEP_TYPES,
    TEST_TASK_STEP_TYPES,
    SQL_STEP_TYPES,
    SUPPORTED_STEP_TYPES,
    TEXT_STEP_TYPES,
)

if TYPE_CHECKING:
    from .api import StepikAPIClient


# ---------------------------------------------------------------------------
# Download: API → local files
# ---------------------------------------------------------------------------

def save_step(
    step_source: dict[str, Any],
    lesson_folder: Path,
    api_client: "StepikAPIClient | None" = None,
    image_downloader: "Callable[[str, Path], None] | None" = None,
) -> dict[str, Any]:
    """Сохраняет шаг локально; возвращает запись для lesson.json."""
    block = step_source.get("block", {})
    step_type = block.get("name", "")
    position = step_source.get("position", 0)

    if step_type not in SUPPORTED_STEP_TYPES:
        raise ValueError(f"Неизвестный тип шага: {step_type!r}")

    folder = step_folder(lesson_folder, position, step_type)
    folder.mkdir(parents=True, exist_ok=True)

    base_entry: dict[str, Any] = {
        "position": position,
        "step_source_id": step_source.get("id"),
        "type": step_type,
        "cost": step_source.get("cost", 0),
    }

    if step_type in TEXT_STEP_TYPES:
        _write_html(folder / "task.html", block.get("text", ""), folder, image_downloader)
        return base_entry

    if step_type in FREE_ANSWER_STEP_TYPES:
        return {**base_entry, **_save_free_answer(step_source, block, folder, api_client, image_downloader)}

    if step_type in CODE_STEP_TYPES:
        _save_code(block, folder, image_downloader)
        return base_entry

    if step_type in DATASET_STEP_TYPES:
        _save_dataset(block, folder, image_downloader)
        return base_entry

    if step_type in SQL_STEP_TYPES:
        _save_sql(block, folder, image_downloader)
        return base_entry

    if step_type in HTML_TASK_STEP_TYPES:
        _save_html_task(block, folder, image_downloader)
        return base_entry

    if step_type in TEST_TASK_STEP_TYPES:
        _save_question(block, folder, step_type, image_downloader)
        return base_entry

    raise ValueError(f"Неизвестный тип шага: {step_type!r}")


def delete_step_folder(lesson_folder: Path, position: int, step_type: str) -> None:
    """Удаляет подпапку шага если она существует."""
    folder = step_folder(lesson_folder, position, step_type)
    if folder.exists():
        shutil.rmtree(folder)


# --- type-specific writers --------------------------------------------------

def _save_free_answer(
    step_source: dict[str, Any],
    block: dict[str, Any],
    folder: Path,
    api_client: "StepikAPIClient | None",
    image_downloader: "Callable[[str, Path], None] | None" = None,
) -> dict[str, Any]:
    _write_html(folder / "task.html", block.get("text", ""), folder, image_downloader)
    source = block.get("source", {})
    extra: dict[str, Any] = {
        "is_attachments_enabled": source.get("is_attachments_enabled", False),
        "is_html_enabled": source.get("is_html_enabled", True),
        "manual_scoring": source.get("manual_scoring", False),
    }
    instruction_id = step_source.get("instruction")
    instruction_type = step_source.get("instruction_type")
    if instruction_id and instruction_type and api_client is not None:
        instruction = api_client.get_instruction(instruction_id)
        _save_instruction(folder, instruction)
        extra["instruction_id"] = instruction_id
        extra["instruction_type"] = instruction_type
    return extra


def _save_instruction(folder: Path, instruction: dict[str, Any]) -> None:
    data = {
        "strategy_type": instruction.get("strategy_type", "peer"),
        "min_reviews": instruction.get("min_reviews", 1),
        "text": instruction.get("text", ""),
        "rubrics": [
            {"text": r.get("text", ""), "cost": r.get("cost", 1), "position": r.get("position", i + 1)}
            for i, r in enumerate(instruction.get("rubrics", []))
        ],
    }
    _write_json(folder / "instruction.json", data)


def _save_code(
    block: dict[str, Any],
    folder: Path,
    image_downloader: "Callable[[str, Path], None] | None" = None,
) -> None:
    _write_html(folder / "task.html", block.get("text", ""), folder, image_downloader)
    options = block.get("options", {})
    source = block.get("source", {})
    checker_code = source.get("code", "")
    if checker_code:
        (folder / "checker.py").write_text(checker_code, encoding="utf-8")
    meta = {
        "time_limit": options.get("execution_time_limit", 5),
        "memory_limit": options.get("execution_memory_limit", 256),
        "limits": options.get("limits", {}),
        "templates": options.get("code_templates", {}),
        "header_lines": options.get("code_templates_header_lines_count", {}),
        "footer_lines": options.get("code_templates_footer_lines_count", {}),
        "samples": options.get("samples", []),
        "samples_count": source.get("samples_count", 0),
        "is_run_user_code_allowed": options.get("is_run_user_code_allowed", True),
        "templates_data": source.get("templates_data", ""),
        "is_time_limit_scaled": source.get("is_time_limit_scaled", True),
        "is_memory_limit_scaled": source.get("is_memory_limit_scaled", True),
        "manual_time_limits": source.get("manual_time_limits", []),
        "manual_memory_limits": source.get("manual_memory_limits", []),
        "test_cases": source.get("test_cases", []),
    }
    _write_json(folder / "step.json", meta)


def _save_dataset(
    block: dict[str, Any],
    folder: Path,
    image_downloader: "Callable[[str, Path], None] | None" = None,
) -> None:
    _write_html(folder / "task.html", block.get("text", ""), folder, image_downloader)
    options = block.get("options", {})
    source = block.get("source", {})
    code = source.get("code", "")
    if code:
        (folder / "dataset.py").write_text(code, encoding="utf-8")
    meta = {
        "samples": options.get("samples", []),
        "time_limit": options.get("time_limit", 300),
        "is_time_limit_enabled": source.get("is_time_limit_enabled", True),
    }
    _write_json(folder / "step.json", meta)


def _save_sql(
    block: dict[str, Any],
    folder: Path,
    image_downloader: "Callable[[str, Path], None] | None" = None,
) -> None:
    _write_html(folder / "task.html", block.get("text", ""), folder, image_downloader)
    options = block.get("options", {})
    source = block.get("source", {})
    (folder / "init.sql").write_text(source.get("init_sql", ""), encoding="utf-8")
    (folder / "solve.sql").write_text(source.get("solve_sql", ""), encoding="utf-8")
    check_code = source.get("check_code", "")
    if check_code:
        (folder / "checker.py").write_text(check_code, encoding="utf-8")
    meta = {
        "is_multiple_statements_allowed": source.get("is_multiple_statements_allowed", False),
        "is_run_user_code_allowed": source.get("is_run_user_code_allowed", options.get("is_run_user_code_allowed", True)),
    }
    _write_json(folder / "step.json", meta)


def _save_html_task(
    block: dict[str, Any],
    folder: Path,
    image_downloader: "Callable[[str, Path], None] | None" = None,
) -> None:
    _write_html(folder / "task.html", block.get("text", ""), folder, image_downloader)
    options = block.get("options", {})
    source = block.get("source", {})
    html_tmpl = source.get("html_template", options.get("html_template", ""))
    css_tmpl = source.get("css_template", options.get("css_template", ""))
    (folder / "template.html").write_text(html_tmpl, encoding="utf-8")
    (folder / "template.css").write_text(css_tmpl, encoding="utf-8")
    meta = {
        "checklist": source.get("checklist", options.get("checklist", [])),
    }
    _write_json(folder / "step.json", meta)


def _save_question(
    block: dict[str, Any],
    folder: Path,
    step_type: str,
    image_downloader: "Callable[[str, Path], None] | None" = None,
) -> None:
    text = block.get("text", "")
    if image_downloader is not None:
        image_downloader(text, folder)
    source = block.get("source", {})
    data: dict[str, Any] = {"text": text}

    if step_type == "choice":
        data.update({
            "is_multiple_choice": source.get("is_multiple_choice", False),
            "preserve_order": source.get("preserve_order", False),
            "sample_size": source.get("sample_size", len(source.get("options", []))),
            "is_html_enabled": source.get("is_html_enabled", True),
            "is_options_feedback": source.get("is_options_feedback", False),
            "options": source.get("options", []),
        })
    elif step_type == "sorting":
        data.update({
            "is_html_enabled": source.get("is_html_enabled", False),
            "options": source.get("options", []),
        })
    elif step_type == "matching":
        data.update({
            "preserve_firsts_order": source.get("preserve_firsts_order", True),
            "pairs": source.get("pairs", []),
        })
    elif step_type == "fill-blanks":
        data.update({
            "is_case_sensitive": source.get("is_case_sensitive", False),
            "is_detailed_feedback": source.get("is_detailed_feedback", False),
            "is_partially_correct": source.get("is_partially_correct", False),
            "components": source.get("components", []),
        })
    elif step_type == "number":
        data["options"] = source.get("options", [])
    elif step_type == "string":
        data.update({
            "pattern": source.get("pattern", ""),
            "use_re": source.get("use_re", False),
            "match_substring": source.get("match_substring", False),
            "case_sensitive": source.get("case_sensitive", False),
            "code": source.get("code", ""),
            "is_text_disabled": source.get("is_text_disabled", False),
            "is_file_disabled": source.get("is_file_disabled", True),
        })
    elif step_type == "random-tasks":
        data.update({
            "task": source.get("task", ""),
            "solve": source.get("solve", ""),
            "max_error": source.get("max_error", "0"),
            "ranges": source.get("ranges", []),
            "combinations": source.get("combinations", 1),
        })
    elif step_type == "math":
        data.update({
            "answer": source.get("answer", ""),
            "numerical_test": source.get("numerical_test", {}),
        })
    elif step_type == "table":
        data.update({
            "columns": source.get("columns", []),
            "rows": source.get("rows", []),
            "options": source.get("options", {}),
            "description": source.get("description", ""),
            "is_always_correct": source.get("is_always_correct", False),
        })

    data["feedback_correct"] = block.get("feedback_correct", "")
    data["feedback_wrong"] = block.get("feedback_wrong", "")
    _write_json(folder / "step.json", data)


# ---------------------------------------------------------------------------
# Upload: local files → Stepik block
# ---------------------------------------------------------------------------

def load_step_instruction(
    manifest_entry: dict[str, Any],
    lesson_folder: Path,
) -> dict[str, Any] | None:
    """Читает instruction.json для free-answer шага.

    Возвращает dict с полями instruction_type, instruction_id (если есть)
    и данными для создания/обновления инструкции, либо None если не применимо.
    """
    if manifest_entry.get("type") != "free-answer":
        return None
    instruction_type = manifest_entry.get("instruction_type")
    if not instruction_type:
        return None
    step_type = manifest_entry["type"]
    position = manifest_entry["position"]
    folder = step_folder(lesson_folder, position, step_type)
    instr_file = folder / "instruction.json"
    if not instr_file.exists():
        return None
    data = json.loads(instr_file.read_text(encoding="utf-8"))
    return {
        "instruction_type": instruction_type,
        "instruction_id": manifest_entry.get("instruction_id"),
        "data": data,
    }


def load_step(
    manifest_entry: dict[str, Any],
    lesson_folder: Path,
) -> tuple[dict[str, Any], int, str]:
    """Читает локальные файлы шага; возвращает (block, cost, label)."""
    step_type = manifest_entry["type"]
    position = manifest_entry["position"]
    cost = manifest_entry.get("cost", 0)
    folder = step_folder(lesson_folder, position, step_type)

    if step_type in TEXT_STEP_TYPES:
        block, label = _load_text(folder)
    elif step_type in FREE_ANSWER_STEP_TYPES:
        block, label = _load_free_answer(manifest_entry, folder)
    elif step_type in CODE_STEP_TYPES:
        block, label = _load_code(folder)
    elif step_type in DATASET_STEP_TYPES:
        block, label = _load_dataset(folder)
    elif step_type in SQL_STEP_TYPES:
        block, label = _load_sql(folder)
    elif step_type in HTML_TASK_STEP_TYPES:
        block, label = _load_html_task(folder)
    elif step_type in TEST_TASK_STEP_TYPES:
        block, label = _load_question(folder, step_type)
    else:
        raise ValueError(f"Неизвестный тип шага: {step_type!r}")

    return block, cost, label


def _load_text(folder: Path) -> tuple[dict[str, Any], str]:
    html = _read_html(folder / "task.html")
    block = {"name": "text", "text": _strip_comments(html), "video": None,
             "source": {}, "feedback_correct": "", "feedback_wrong": ""}
    return block, _title(html)


def _load_free_answer(
    manifest_entry: dict[str, Any], folder: Path
) -> tuple[dict[str, Any], str]:
    html = _read_html(folder / "task.html")
    block: dict[str, Any] = {
        "name": "free-answer",
        "text": _strip_comments(html),
        "video": None,
        "source": {
            "is_attachments_enabled": manifest_entry.get("is_attachments_enabled", False),
            "is_html_enabled": manifest_entry.get("is_html_enabled", True),
            "manual_scoring": manifest_entry.get("manual_scoring", False),
        },
        "feedback_correct": "",
        "feedback_wrong": "",
    }
    return block, _title(html)


def _load_code(folder: Path) -> tuple[dict[str, Any], str]:
    html = _read_html(folder / "task.html")
    meta = _read_json(folder / "step.json")
    checker = (folder / "checker.py").read_text(encoding="utf-8") if (folder / "checker.py").exists() else ""
    options = {
        "execution_time_limit": meta.get("time_limit", 5),
        "execution_memory_limit": meta.get("memory_limit", 256),
        "limits": meta.get("limits", {}),
        "code_templates": meta.get("templates", {}),
        "code_templates_header_lines_count": meta.get("header_lines", {}),
        "code_templates_footer_lines_count": meta.get("footer_lines", {}),
        "samples": meta.get("samples", []),
        "is_run_user_code_allowed": meta.get("is_run_user_code_allowed", True),
    }
    source = {
        "code": checker,
        "execution_time_limit": meta.get("time_limit", 5),
        "execution_memory_limit": meta.get("memory_limit", 256),
        "samples_count": meta.get("samples_count", 0),
        "templates_data": meta.get("templates_data", ""),
        "is_time_limit_scaled": meta.get("is_time_limit_scaled", True),
        "is_memory_limit_scaled": meta.get("is_memory_limit_scaled", True),
        "is_run_user_code_allowed": meta.get("is_run_user_code_allowed", True),
        "manual_time_limits": meta.get("manual_time_limits", []),
        "manual_memory_limits": meta.get("manual_memory_limits", []),
        "test_archive": [],
        "test_cases": meta.get("test_cases", []),
    }
    block = {"name": "code", "text": _strip_comments(html), "video": None,
             "options": options, "source": source,
             "feedback_correct": "", "feedback_wrong": ""}
    return block, _title(html)


def _load_dataset(folder: Path) -> tuple[dict[str, Any], str]:
    html = _read_html(folder / "task.html")
    meta = _read_json(folder / "step.json")
    code = (folder / "dataset.py").read_text(encoding="utf-8") if (folder / "dataset.py").exists() else ""
    block = {
        "name": "dataset",
        "text": _strip_comments(html),
        "video": None,
        "options": {"samples": meta.get("samples", []), "time_limit": meta.get("time_limit", 300)},
        "source": {"code": code, "is_time_limit_enabled": meta.get("is_time_limit_enabled", True)},
        "feedback_correct": "", "feedback_wrong": "",
    }
    return block, _title(html)


def _load_sql(folder: Path) -> tuple[dict[str, Any], str]:
    html = _read_html(folder / "task.html")
    meta = _read_json(folder / "step.json")
    init_sql = (folder / "init.sql").read_text(encoding="utf-8") if (folder / "init.sql").exists() else ""
    solve_sql = (folder / "solve.sql").read_text(encoding="utf-8") if (folder / "solve.sql").exists() else ""
    checker = (folder / "checker.py").read_text(encoding="utf-8") if (folder / "checker.py").exists() else ""
    block = {
        "name": "sql",
        "text": _strip_comments(html),
        "video": None,
        "options": {"is_run_user_code_allowed": meta.get("is_run_user_code_allowed", True)},
        "source": {
            "init_sql": init_sql,
            "solve_sql": solve_sql,
            "check_code": checker,
            "is_multiple_statements_allowed": meta.get("is_multiple_statements_allowed", False),
            "is_run_user_code_allowed": meta.get("is_run_user_code_allowed", True),
        },
        "feedback_correct": "", "feedback_wrong": "",
    }
    return block, _title(html)


def _load_html_task(folder: Path) -> tuple[dict[str, Any], str]:
    html = _read_html(folder / "task.html")
    meta = _read_json(folder / "step.json")
    html_tmpl = (folder / "template.html").read_text(encoding="utf-8") if (folder / "template.html").exists() else ""
    css_tmpl = (folder / "template.css").read_text(encoding="utf-8") if (folder / "template.css").exists() else ""
    checklist = meta.get("checklist", [])
    block = {
        "name": "html",
        "text": _strip_comments(html),
        "video": None,
        "options": {"html_template": html_tmpl, "css_template": css_tmpl, "checklist": checklist},
        "source": {"html_template": html_tmpl, "css_template": css_tmpl, "checklist": checklist},
        "feedback_correct": "", "feedback_wrong": "",
    }
    return block, _title(html)


def _load_question(folder: Path, step_type: str) -> tuple[dict[str, Any], str]:
    data = _read_json(folder / "step.json")
    html = _strip_comments(data.get("text", ""))
    source: dict[str, Any] = {}

    if step_type == "choice":
        source = {
            "options": data.get("options", []),
            "is_multiple_choice": data.get("is_multiple_choice", False),
            "is_always_correct": False,
            "sample_size": data.get("sample_size", len(data.get("options", []))),
            "preserve_order": data.get("preserve_order", False),
            "is_html_enabled": data.get("is_html_enabled", True),
            "is_options_feedback": data.get("is_options_feedback", False),
        }
    elif step_type == "sorting":
        source = {
            "is_html_enabled": data.get("is_html_enabled", False),
            "options": data.get("options", []),
        }
    elif step_type == "matching":
        source = {"pairs": data.get("pairs", []), "preserve_firsts_order": data.get("preserve_firsts_order", True)}
    elif step_type == "fill-blanks":
        source = {
            "components": data.get("components", []),
            "is_case_sensitive": data.get("is_case_sensitive", False),
            "is_detailed_feedback": data.get("is_detailed_feedback", False),
            "is_partially_correct": data.get("is_partially_correct", False),
        }
    elif step_type == "number":
        source = {"options": data.get("options", [])}
    elif step_type == "string":
        source = {
            "pattern": data.get("pattern", ""),
            "use_re": data.get("use_re", False),
            "match_substring": data.get("match_substring", False),
            "case_sensitive": data.get("case_sensitive", False),
            "code": data.get("code", ""),
            "is_text_disabled": data.get("is_text_disabled", False),
            "is_file_disabled": data.get("is_file_disabled", True),
        }
    elif step_type == "random-tasks":
        source = {
            "task": data.get("task", ""),
            "solve": data.get("solve", ""),
            "max_error": data.get("max_error", "0"),
            "ranges": data.get("ranges", []),
            "combinations": data.get("combinations", 1),
        }
    elif step_type == "math":
        source = {"answer": data.get("answer", ""), "numerical_test": data.get("numerical_test", {})}
    elif step_type == "table":
        source = {
            "columns": data.get("columns", []),
            "rows": data.get("rows", []),
            "options": data.get("options", {}),
            "description": data.get("description", ""),
            "is_always_correct": data.get("is_always_correct", False),
        }

    block: dict[str, Any] = {
        "name": step_type,
        "text": html,
        "video": None,
        "source": source,
        "feedback_correct": data.get("feedback_correct", ""),
        "feedback_wrong": data.get("feedback_wrong", ""),
    }
    return block, f"{step_type}: {_title(html)}"


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _write_html(
    path: Path,
    content: str,
    folder: "Path | None" = None,
    image_downloader: "Callable[[str, Path], None] | None" = None,
) -> None:
    path.write_text(content.strip(), encoding="utf-8")
    if image_downloader is not None and folder is not None:
        image_downloader(content, folder)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_html(path: Path) -> str:
    if not path.exists():
        return ""
    html = path.read_text(encoding="utf-8").strip()
    body = re.search(r"<body[^>]*>(.*?)</body>", html, re.IGNORECASE | re.DOTALL)
    return body.group(1).strip() if body else html


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _strip_comments(html: str) -> str:
    return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL).strip()


def _title(html: str, max_length: int = 80) -> str:
    m = re.search(r"<h[1-3][^>]*>(.*?)</h[1-3]>", html, re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", "", (m.group(1) if m else html)).strip()
    return text[:max_length]
