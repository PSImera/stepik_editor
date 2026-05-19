---
name: summary
description: Use when you need to recall what was covered in previous lessons, or to save a summary after finishing a lesson or a module. Contains rules for storing and reading short summaries of finalized lesson steps and for generating or updating module-level plan files.
argument-hint: "[course] [module] [lesson] [script|llm]"
---

# Argument Parsing

Parse `$ARGUMENTS` by recognising these optional tokens in any order:

| Token | Meaning |
|---|---|
| Matches a course name (see list below) | `course` |
| `script` or `llm` | `mode` |
| First remaining number | `module` |
| Second remaining number | `lesson` |

**Known courses** — read at runtime: list all subdirectories of `courses/` (use `Glob` with pattern `courses/*/` or PowerShell `Get-ChildItem courses -Directory`). Do not hardcode course names.

After parsing, ask for any missing required values using `AskUserQuestion`:

1. **course** — if absent or unrecognised, ask with a single-select showing the list of folders inside `courses/`.
2. **module** — if absent, ask as a free-text number input (label: "Модуль").
3. **lesson** — if absent, offer two options: "Урок (ввести номер)" or "Весь модуль". If the user picks "Весь модуль", set scope = module.
4. **mode** — if absent, ask with two options:
   - **script** — быстрая генерация через Python-скрипт (рекомендуется для batch-запуска)
   - **llm** — генерация агентом (читает HTML/JSON, пишет rich summary с контекстом)

Scope is determined by what the user provides:
- course only → **course scope** (all modules and lessons)
- course + module → **module scope**
- course + module + lesson → **lesson scope**

---

# MODE: script

Run the ready-made script with scope-appropriate flags:

| Scope | Command |
|---|---|
| Lesson | `.\.venv\Scripts\python.exe -m src.utils.generate_lesson_summaries --course <course> --module <M> --lesson <L>` |
| Module | `.\.venv\Scripts\python.exe -m src.utils.generate_lesson_summaries --course <course> --module <M>` |
| Course | `.\.venv\Scripts\python.exe -m src.utils.generate_lesson_summaries --course <course>` |

The script:
- Builds a TF-IDF index across all `task.html` files in the course (always full-course for accurate IDF).
- Reads `lesson.json`, step HTML files and `step.json` for quiz steps.
- Writes `<module>-<lesson>_summary.md` next to each `lesson.json`.
- Overwrites existing summaries.
- Accepts optional `--module` and `--lesson` flags to restrict which summaries are written.

**When to use script mode:**
- Generating summaries for one lesson, a module, or the whole course.
- Fast first-pass indexing before authoring new lessons.
- The course already has real lesson content (not stubs).

**After the script finishes:** report how many files were created/updated (parse the script's stdout).

**Stub detection in script mode:** the script generates summaries even for stub lessons — the summary will be thin. If the target lessons are stubs, warn the user and suggest generating a module plan (module mode, llm) instead.

---

# MODE: llm — LESSON SCOPE

## Goal

Create or update `courses/<course>/<module>/<lesson>/<module>-<lesson>_summary.md` using LLM reasoning over actual step content.

## Stub check

Before reading step content, open the first text step's `task.html`. If it contains only placeholder text (e.g. `<p>Урок находится в стадии разработки.</p>` or similar), the lesson is a stub.

**If stub:** do not generate a lesson summary. Instead ask the user:
> Урок — заглушка. Сгенерировать план модуля вместо summary?

If the user agrees, switch to **MODULE MODE** (llm).

## Steps

1. Locate `courses/<course>/<module>/<lesson>/`.
2. Read `lesson.json` to get the step list. For each step:
   - `text` / `code` / `free-answer`: read `{pos:02d}_{type}/task.html`.
   - `choice` / `matching` / `sorting` / `fill-blanks` / `number` / `string` / `math` / `table`: read `{pos:02d}_{type}/step.json`, field `"text"`.
   - Programming task steps: also read files from `practice_prog_<index>/` if present.
3. Check whether `<module>-<lesson>_summary.md` already exists.
   - Exists → update it to match current lesson state.
   - Missing → create it from scratch.

## Where to store

`courses/<course>/<module>/<lesson>/<module>-<lesson>_summary.md`

## What the summary must include

- Short lesson objective.
- Compact lesson structure: how many theory steps, question steps, free-answer steps, and programming tasks (derive from `lesson.json`).
- Main ideas and terms introduced.
- What the learner should already understand after this lesson.
- If a final practical HTML step exists: what it does and what handoff it creates for the next lesson.
- For courses with a cross-course project: current project stage (done / not started / what next lesson should advance), concrete artifacts already in play (key files, documents, folders), and a short practice handoff (what learner-facing action continues next, what prompt/task shape is expected, what observable result the next lesson should target).
- Established terminology and wording conventions.
- What must not be repeated verbatim in the next lesson.
- Which examples, artifacts, or practical accents were already used.

## What the summary must NOT include

- Large copied HTML fragments.
- Full step-by-step lesson transcript.
- Random details that do not help build the next lesson.

## Extra guidance for cross-course practice

A good summary lets the next editor answer three questions without rereading all HTML:
1. Where the shared project currently stands.
2. Which concrete artifacts are already available for reuse.
3. What the next practical move in the project should be.

## Final check (lesson scope)

1. File is in the correct location.
2. Summary reflects the current lesson state.
3. Theory steps, practical steps, and question/assignment artifacts are described accurately.
4. Summary is concise, useful, and reusable for future tasks.

---

# MODE: llm — MODULE SCOPE

## Goal

Create or update `courses/<course>/<module>/<module>_module_plan.md`.

This file is the **navigation anchor for the entire module**. Agents read it before generating new lessons to understand what has been covered, how lessons connect, and what the module promises.

## Step 1 — Detect lesson status

Scan `courses/<course>/<module>/` for lesson subfolders. For each folder, read `lesson.json` and open the first theory step's `task.html`. Classify each lesson as:

| State | Meaning |
|---|---|
| **stub** | Contains only placeholder text |
| **real** | Has actual content |

Classify the module as one of: **all stubs**, **mixed**, **complete**.

## Step 2 — Load Stepik structure (if available)

Look for a `structure.json` under `.cache/stepik/`. Run:

```
.\.venv\Scripts\python.exe -m src.utils.extract_course_structure --input <path-to-structure.json>
```

Find the section whose `section_position` matches the module number. Lesson titles from its `lessons` array are the source of truth.

## Step 3 — Determine the lesson list

**If Stepik structure available:** use those lesson titles. Flag any mismatch between the structure and actual subfolders to the user.

**If no Stepik structure and module has stubs or is empty:** propose a coherent list of 4–6 lessons that logically fills the module's role in the course arc. **Wait for user confirmation before generating the plan.**

## Step 4 — Gather content

- **Complete module:** read each `<module>-<lesson>_summary.md`. If a lesson summary is missing, run lesson-scope llm mode for that lesson first.
- **Mixed module:** use lesson summaries for completed lessons; describe stub lessons from the confirmed lesson list.
- **All-stubs module:** the plan is a planning document. Use the confirmed lesson list to draft the structure.

## Step 5 — Write or update `<module>_module_plan.md`

File path: `courses/<course>/<module>/<module>_module_plan.md`.

### Required sections

```markdown
# План модуля <N> — актуальное состояние

## Модуль <N>: `<module title>`

<2–3 sentences: what problem this module solves, how it fits into the course arc,
 connection to the previous and next modules.>

Сквозная рамка модуля: <1–2 sentences: the conceptual spine connecting all lessons.>

## Краткая логика модуля

<Numbered list 4–6 items: a narrative of how understanding builds — not just lesson titles.>

## Статус уроков

<One-line status summary.>

## Структура модуля

### Урок <module>-<lesson>. `<lesson title>`

**Статус: <сгенерирован | не начат | частично готов>**

<Completed lessons: paste or summarise from lesson summary.
 Stub/planned lessons: describe role and planned content, mark as planned.>

Актуальная структура урока:
- `01_text` — <what this step covers>
- ...

---

## Сквозная практика в модуле   ← include only if the course has a recurring practice framework

<How the recurring practice element (e.g. a project, a framework, a workflow) is used across the module's practice steps.>

## Что должен уметь студент после модуля

<Numbered list of 5–8 concrete skills. Use "умеет", "понимает", "может объяснить".>

## Что важно удержать при дальнейшем редактировании

<Bullet list: editorial constraints, things to avoid, mistakes to guard against,
 step-count limit reminder (no more than 16 steps per lesson).>
```

### Tone

- **Complete module:** match detail level of `08_module_plan.md` — include actual step content.
- **Stub/planned module:** match detail level of `09_module_plan.md` — mark planned content clearly.

## Step 6 — Final check (module scope)

1. File is at the correct path.
2. Module title and lesson titles match the Stepik structure (if available).
3. Lesson statuses accurately reflect actual file state.
4. "Краткая логика" reads as a coherent narrative.
5. "Что важно удержать" contains the 16-step limit reminder.
6. If the course has a recurring practice framework: "Сквозная практика" section is present and consistent with practice steps.
7. No lesson is described as completed if its HTML files are stubs.

---

# How to use module plans

- Before creating a new lesson, read the module plan to understand what has been covered and what remains.
- Before planning a new module, read plans of the two or three preceding modules to avoid duplication.
- If the module plan is absent or outdated, run `/summary <course> <module> llm` before authoring.
- If lesson summaries are absent for completed lessons, run `/summary <course> <module> <lesson> llm` for each lesson before updating the module plan.
