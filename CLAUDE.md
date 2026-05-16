# AGENTS.md

Short routing rules for working with learning materials in the `stepik_editor` project.

## Global Constraints
- Communication with the user must be in Russian.
- For local Python commands in this repository, use the project interpreter `.\.venv\Scripts\python.exe` instead of system `python`.
- Always read and write HTML files in `UTF-8`.

## Shell and File System (Windows)
- The environment is **Windows**. Use the dedicated tools `Read`, `Glob`, `Grep` for all file reads — never `ls`, `cat`, `find`, or `grep` via Bash.
- **Always use the PowerShell tool for any shell command** — this is not optional. Bash cannot resolve Windows backslash paths and will fail silently or with "command not found".
- Never mix forward slashes in PowerShell paths; they cause "cannot access" errors on Windows.
- The Bash tool is completely off-limits for any command that references local project paths or the `.venv` interpreter.

## Base Context
- Read `course_config.json` to get `default_course`; use it as the active course unless the user specifies otherwise.
- All courses are stored in `courses/`.
- The base structure is: `courses/<course>/<module>/<lesson>/`.
- Module and lesson folders use zero-padded indices like `03/05`.
- A lesson is a sequence of steps with one shared numbering space. The authoritative step list is in `lesson.json` at the lesson root.
- Each step is stored in its own subfolder `{pos:02d}_{type}/` inside the lesson folder, e.g. `01_text/`, `05_choice/`, `03_code/`.
- **Step number** = `position` field in `lesson.json`. When the user says "шаг 5" or "step 10", that is the position number.
- **Step type** is the folder suffix after the underscore: `text`, `choice`, `sorting`, `matching`, `fill-blanks`, `number`, `string`, `math`, `table`, `code`, `free-answer`, `dataset`, `sql`, `html`.
- To find step N: look up position N in `lesson.json`, read the `type` field, then open `courses/<course>/<module>/<lesson>/{N:02d}_{type}/`.
- When the user says "сделай шаг 10 задачей на программирование" — create/rename the subfolder for position 10 to `10_code/` and update `lesson.json` accordingly.
- Before editing, identify the exact course/module/lesson/step path.
- Do not change neighboring lessons, modules, or courses unless required.
- Do not run large-scale refactors if the task targets only one lesson.
- Theory steps, each тестовая задача step, and each task step all belong to that same lesson-step sequence.
- When тестовые задачи or tasks are added after theory steps, their indices must continue the lesson-step numbering after the existing theory steps.
- Practical tasks may also be grouped into a separate lesson of the module that contains only tasks, including automatically checked programming tasks and human-reviewed tasks.
- The total number of lesson steps inside any one lesson, including theory steps, each тестовая задача step, and each task step, must not exceed `16`.
- Сode examples that need separate validation are stored next to the lesson materials in `courses/<course>/<module>/<lesson>/code_examples/<step>/`.
- Image assets for a step are stored directly inside its step subfolder, numbered sequentially: `01.<ext>`, `02.<ext>`, etc. For example `courses/<course>/<module>/<lesson>/01_text/01.png`.
- Text and task steps store their content in `task.html` inside the step subfolder.
- Тестовые задачи (choice, sorting, matching, fill-blanks, number, string, math, table) are stored as `step.json` only — no `task.html`.

## Skills

- Load skills only on demand for the current task.
- If the task edits `CLAUDE.md` or any skill file in `.claude/skills/`, treat it as an edit-rules task before applying any more specific skill.
- If `docs/<course>.md` exists for the target course, read it and apply those rules together with the selected skill.

## Course structure

- Before editing materials, identify the target course.
- If a course-specific rules file references a cached Stepik `structure.json`, do not read the raw cache file directly for routine authoring context. Use `python -m src.utils.extract_course_structure --input <path-to-structure.json>` and rely on its compact output.
- When such parsed Stepik structure is available, use it as the source of truth for `course_name`, course description fields, module titles, and lesson titles.
- Course-specific rules are additive and should only affect tasks inside that course.
- If no course-specific rules file exists, continue with the general rules only.
