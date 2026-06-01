---
name: task-programming
description: Rules for creating automatically checked programming tasks for a specific lesson.
---

## Purpose

- Apply these rules when the user asks to create a programming assignment that is solved on the platform and checked automatically.
- The condition file is public learner-facing content. **Always use /public-materials skill** together with these rules when writing or editing `taskN_condition.html`.
- Use the lesson theory as the source for the target concept, scope, and expected difficulty.
- Keep the assignment focused on one lesson inside one module and one course.

## Where To Store Programming Tasks

- Store each programming task inside the folder of the lesson it belongs to.
- For each new task, create a dedicated subfolder named `{pos:02d}_code/`, where `{pos:02d}` is the zero-padded position number from `lesson.json` — the same convention used by all other step folders (`01_text`, `03_choice`, etc.).
- Keep all files related to that automatically checked programming task inside the corresponding `{pos:02d}_code/` folder.
- After creating the files, add the step entry to `lesson.json`: `{"position": <pos>, "step_source_id": null, "type": "code", "cost": 1}`. Use the next available position after existing steps.

## Required Files

Store the following files inside `{pos:02d}_code/`. The names are fixed — the uploader looks for exactly these names:

- `task.html` — condition shown to the student (public-facing, use /public-materials rules)
- `template.py` — full template with `::python3`, `::header`, `::code`, `::footer` markers. **This is the single source of truth for the template** — the uploader reads `templates_data` directly from this file. Do NOT duplicate its content into `step.json`.
- `checker.py` — checker module with `generate`, `solve`, `check` (runs on Python 3.6)
- `solution.py` — reference solution (local authoring only, not uploaded)
- `step.json` — step metadata (limits, flags); **must be created manually** (see format below)

## step.json Format

`step.json` holds only the uploader metadata for a code step — **not** the template, which lives in `template.py`. Create it alongside `template.py`:

```json
{
    "time_limit": 8,
    "memory_limit": 256,
    "limits": {},
    "templates": {},
    "header_lines": {},
    "footer_lines": {},
    "samples": [],
    "samples_count": 0,
    "is_time_limit_scaled": true,
    "is_memory_limit_scaled": true,
    "manual_time_limits": [],
    "manual_memory_limits": [],
    "test_cases": [],
    "is_run_user_code_allowed": true
}
```

- Do **not** add a `templates_data` key — the uploader (`_load_code` in `src/stepik_downloader/step_storage.py`) reads the template from `template.py` directly. If a task has no template (a simple task without `::header`/`::footer`), just omit `template.py` and the uploaded template stays empty.
- Leave `templates`, `header_lines`, `footer_lines` as empty objects `{}` on first upload — Stepik parses the `::header`/`::code`/`::footer` markers server-side and fills them.
- Adjust `time_limit` (seconds) to the task complexity: 5 s for simple loops, 8–15 s for tasks with I/O or mocking.
- `step.json` has no multiline strings now, so it can be written directly without a helper script.

## Condition File Requirements

- Use rules for Condition part together with /public-materials skill.
- `task.html` is formatted the same way as lesson step HTML files: **no `<!DOCTYPE>`, `<html>`, `<head>`, or `<body>` tags** — content starts directly with `<h1>`.
- `taskN_condition.html` must include:
    - `<h1>` with the task title;
    - `<h2>Задание</h2>` with a clear statement of what to implement;
    - a description of special or edge cases when relevant;
    - `<h2>Примечание</h2>` when needed.
- In the note, **mention pre-defined helpers only when they are not self-evident from the task body.** If the task description already names a function and explains what it does (e.g. "Функция `load_data()` возвращает список записей..."), repeating "it is already available" is redundant — omit it. Do mention in the note: (a) an environment variable name if the header reads one (e.g. `API_KEY`); (b) any pre-defined helper that the task body does not describe but the student might need. **Always use the exact name**: say "`_cache` и `_state` уже объявлены", never "глобальные переменные уже объявлены" without naming them. Do NOT tell the student to define something themselves (like `MAX_SIZE`) — if it is not in the template, they figure it out from the task body.
- In the note, specify when relevant:
    - that input is already parsed and passed as function arguments;
    - which libraries are already imported;
    - argument data types such as `list`, `set`, or `dict`;
    - that output formatting is handled automatically and the student should not call the function manually.
- Do not include:
    - `<h2>Пример</h2>` heading or any example block — the platform automatically inserts test #1 from `generate()` as the example on the task page;
    - tables of input/output examples;
    - multiple examples.

## Template File Requirements

- `taskN_template.py` must target Python `3.12`.
- The template must use the hidden sections `::header`, `::code`, and `::footer`.
- **Section markers are plain text directives, NOT Python comments.** Write `::header`, `::code`, `::footer` without a leading `#`. A `# ::footer` is a Python comment and will be ignored by the platform — the footer will never run.
- The first line of the file must be the Python version directive (no `#`): `::python3` targets Python 3.x (actual version depends on the platform default), `::python3.12` explicitly enables Python 3.12. Use `::python3.12` when the template or solution uses 3.12-only syntax. See `practice_prog_example_2/template.py` for a working reference.
- `::header` is prepended before student code and `::footer` is appended after it.
- Hidden templates are used for imports, helper definitions, input/output handling, code restrictions, and additional checks.
- `::header` must contain only imports.
- `::code` must contain the student function and that function must be defined first.
- `::footer` must contain input parsing, calling the student function, and output formatting after the function definition.
- Prefer input parsing based on `splitlines()` semantics.
- All comments in the template (hints, step comments inside `::code`) must be in Russian.
- Template and solution may use Python 3.12 syntax (`list[str]`, `dict[str, int]`, etc.) only when the directive is `::python3.12`.

## Checker File Requirements

- `taskN_checker.py` must be a single self-contained Python module.
- It must define the functions `generate`, `solve`, and `check`.
- **The checker always runs on Python 3.6**, regardless of the `::python3` marker in the template. This is a fixed platform constraint, not configurable.
- Therefore all type annotations in the checker must use `from typing import List, Dict, Tuple, Optional` etc. instead of the built-in generics (`list[str]`, `dict[str, int]`, `tuple[bool, str]`). Using `list[str]` in the checker causes `TypeError: 'type' object is not subscriptable` and breaks `generate`. See `practice_prog_example_1/checker.py` and `practice_prog_example_2/checker.py` for working references.
- `generate` must return from `1` to `100` tests.
- `generate` may return either:
- a list of `dataset` strings;
- a list of `(dataset, clue)` pairs where `clue` is JSON-serializable.
- The first generated test must match the example from the task statement.
- `generate` must cover normal cases and edge cases, including empty input, minimum values, maximum values, and special conditions when applicable.
- Static test lists are allowed when they are appropriate for the task.
- `solve` must accept one `dataset: str` and return the correct formatted answer as `str`.
- `solve` serves as the author solution for consistency checking and as a fallback source for `clue` when `generate` does not provide one.
- `check` must validate one student reply for one test and return either `bool` or `(bool, feedback)`.
- `check` may compare exact output or use another explicit validation rule when the task allows more than one valid answer.
- If multiple correct answers are possible, prefer using `clue` to preserve the acceptable answer space.
- Use `splitlines()` instead of `split('\n')`.
- Keep all helper logic required for checking in the same file.

## Solution File Requirements

- `taskN_solution.py` must contain only one function with the most compact or optimal reference solution.
- Include a short docstring.
- Include only brief comments for key steps, around `2-5` short comment lines in total when comments are needed.
- All comments and docstrings must be in Russian.
- Do not include alternative solutions.
- Do not include usage examples.
- Do not include long explanations.

## Task Requirements

- The task must check one key concept from the lesson without unnecessary extra complexity.
- The task should be realistic, educational, and solvable from the lesson material.
- Supported difficulty bands:
- basic: basic data structures and simple formulas;
- medium: combined data structures, conditions, and loops;
- high: algorithms, optimization, or more complex logic.
- Use only standard library Python `3.12` plus explicitly allowed external libraries.
- If a needed library is not available but the task still requires its interface, imitate it with mock functions, variables, or classes.

## Allowed Libraries

- Allowed external libraries are:
- `beautifulsoup4==4.12.3`
- `django==5.0.6`
- `djangorestframework==3.15.1`
- `emoji==2.11.1`
- `factory-boy==3.3.0`
- `faker==25.0.1`
- `fastapi==0.111.0`
- `flask==3.0.3`
- `flask_restful==0.3.10`
- `flask-smorest==0.44.0`
- `flask_wtf==1.2.1`
- `hypothesis==6.100.4`
- `loguru==0.7.2`
- `lxml==5.2.1`
- `matplotlib==3.10.0`
- `mip==1.14.2`
- `myhdl==0.11.45`
- `mysqlclient==2.2.4`
- `networkx==3.3`
- `numpy==2.2.3`
- `nltk==3.8.1`
- `opencv-python-headless==4.11.0.86`
- `pandas==2.2.3`
- `prettytable==3.10.0`
- `pycosat==0.6.6`
- `pydantic==2.7.1`
- `pymorphy2==0.9.1`
- `pymorphy2_dicts_ru==2.4.417127.4579844`
- `pymystem3==0.2.0`
- `pysqlite3-binary==0.5.4`
- `pytest==8.2.0`
- `python-sat==1.8.dev12`
- `requests==2.31.0`
- `rsa==4.9`
- `shapely==2.0.4`
- `sqlalchemy==2.0.30`
- `sqlmodel==0.0.18`
- `sumy==0.11.0`
- `scikit-image==0.25.1`
- `scikit-learn==1.6.1`
- `scipy==1.15.1`
- `sympy==1.12`
- `toolz==0.12.1`

## Automatic Checking Requirements

- The task must be intended for automatic checking on the platform.
- The solution format, parser logic, and output requirements must be unambiguous.
- The first generated test must correspond to the example from the statement.
- The checker must cover normal cases and edge cases.
- The checker must remain fully self-contained in one file.

## Alignment With The Lesson

- The task must be derived from the actual lesson materials of the same lesson.
- Do not introduce dependencies on concepts not taught in the lesson unless the user explicitly asks for extension.
- Keep terminology consistent with the lesson.
- Match the complexity level to the lesson stage.

## Final Check

1. Ensure the exact lesson path was identified before creating files.
2. Ensure the task folder is named `{pos:02d}_code/` matching the step position in `lesson.json`.
3. Ensure all required files exist: `task.html`, `template.py`, `checker.py`, `solution.py`, `step.json`.
4. Ensure the template lives only in `template.py` and `step.json` has **no** `templates_data` key (the uploader reads the template from `template.py`).
5. Ensure the task is intended for automatic checking, not for manual review.
6. Ensure the condition does not include a `<h2>Пример</h2>` block or multiple examples — the platform inserts test #1 automatically.
7. Ensure the template starts with `::python3` and uses `::header`, `::code`, `::footer` markers **without** a leading `#` — `# ::footer` is a Python comment and breaks execution.
8. Ensure the checker defines `generate`, `solve`, and `check` and is internally consistent.
9. Ensure all type annotations in the checker use `typing` module types (`List`, `Tuple`, `Optional`, etc.), not built-in generics — the checker runs on Python 3.6.
10. Ensure only allowed libraries are used, or absent ones are explicitly mocked.
11. Ensure the statement, template, checker, and solution are consistent with one another.
12. Ensure `lesson.json` has been updated with the new step entry (position, type `code`, step_source_id `null`).
