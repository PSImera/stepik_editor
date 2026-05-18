---
name: course
description: Use for course-level editing: course description fields, module titles and order, lesson titles and order. All changes are made in structure.json and can be uploaded to Stepik via upload_structure().
argument-hint: "[course_name]"
---

## Purpose

This skill handles structural and metadata editing at the course level — above individual lessons. It edits `courses/<course>/structure.json` which is the local source of truth for everything the `upload_structure()` uploader pushes to Stepik.

Course description fields (`description`, `summary`, `target_audience`, `requirements`, `learning_format`, `course_format`, `workload`) are **public-facing text** visible to learners. **Always load /public-materials alongside this skill** when editing any of these fields — the same quality rules (natural Russian, no slop, no unnecessary English terms) apply as for lesson steps.

Use this skill when the task involves:
- Editing course description fields (title, summary, description, target_audience, requirements, etc.)
- Renaming modules or lessons
- Reordering modules or lessons
- Adding new module or lesson entries to the structure
- Reviewing the overall course structure

Do **not** use this skill for editing lesson step content (HTML, quiz questions) — use `/lesson` for that.

---

## Setup

1. Parse `$ARGUMENTS` for a course name. If absent or ambiguous, list subdirectories of `courses/` and ask the user to choose.
2. Read `courses/<course>/structure.json` — this is the single file all edits go to.
3. If a `courses/<course>/CLAUDE.md` exists, read it for course-specific constraints.
4. Confirm the active course and summarise the current structure to the user before making changes:
   - Course title
   - Module count and their titles
   - Lesson count per module

---

## Data Model in structure.json

```
course_info          ← course-level description fields
structure[]          ← array of modules (sections), sorted by section_position
  section_id         ← Stepik ID (0 or absent = not yet created on Stepik)
  section_title      ← editable module title
  section_position   ← order in course (1-based)
  section_info       ← full Stepik API response (do not edit manually)
  lessons[]          ← array of lessons in this module, sorted by position
    lesson_id        ← Stepik ID (0 = not yet created on Stepik)
    unit_id          ← Stepik unit ID (0 = not yet linked)
    lesson_title     ← editable lesson title
    position         ← order within module (1-based)
    lesson_info      ← full Stepik API response (do not edit manually)
    unit_info        ← full Stepik API response (do not edit manually)
```

**Do not touch** `section_info`, `lesson_info`, `unit_info` — these are caches of Stepik API responses, overwritten on next `refresh_structure()`. Edit only the fields listed as "editable".

---

## Editing Rules

### Course Description Fields (`course_info`)

Fields that `upload_structure()` will push to Stepik:

| Field | Type | Notes |
|---|---|---|
| `title` | str | Course title |
| `summary` | str | One-paragraph overview shown in catalog |
| `description` | HTML | Full rich description on course page |
| `target_audience` | str | Who the course is for |
| `requirements` | HTML | Prerequisites |
| `workload` | str | Expected time commitment |
| `certificate` | str | Certificate conditions |
| `intro` | str | Intro video URL |
| `course_format` | str | Format description |

Edit these fields directly in `course_info`. Leave other `course_info` fields untouched (they are technical Stepik fields).

When editing `description` or `requirements`, preserve valid HTML structure. Use `<p>`, `<ul>`, `<li>`, `<strong>` — the same tags Stepik renders.

### Renaming a Module

Update `section_title` of the target entry. Do not change `section_position` unless also reordering.

### Renaming a Lesson

Update `lesson_title` of the target entry inside its module's `lessons` array. Do not change `lesson_id` or `position` unless also reordering.

### Reordering Modules

Change `section_position` values so they form a contiguous sequence starting at 1 with no gaps. Re-sort the `structure` array by `section_position` after editing.

Example — move module 3 to position 1:
- Old: positions 1, 2, 3, 4
- New: positions 2, 3, 1, 4 → after normalisation: 1=old3, 2=old1, 3=old2, 4=old4

Always normalise positions to a gap-free 1-based sequence before saving.

### Reordering Lessons Within a Module

Change `position` values inside the target module's `lessons` array. Normalise to a gap-free 1-based sequence. Re-sort the array by `position` after editing.

### Adding a New Module

Append a new entry to `structure` with:
```json
{
  "section_title": "<title>",
  "section_position": <next available position>,
  "lessons": []
}
```
`section_id` absent or 0 — uploader will create it on Stepik.

### Adding a New Lesson

Append a new entry to the target module's `lessons` array with:
```json
{
  "lesson_id": 0,
  "lesson_title": "<title>",
  "position": <next available position>
}
```
`lesson_id: 0` signals to the uploader that the lesson must be created on Stepik.

---

## What the Uploader Does With Your Changes

After editing `structure.json`, the changes can be pushed to Stepik with:

```python
downloader.upload_structure()          # только структура
downloader.upload_course(sync_structure=True)  # структура + шаги
```

Uploader behaviour:
- **Course description** (`course_info` editable fields) → PUT /api/courses/{id}
- **Module title/position** with existing `section_id` → PUT /api/sections/{id}
- **Module** without `section_id` → POST /api/sections (creates new)
- **Lesson title** with existing `lesson_id` → PUT /api/lessons/{id}
- **Lesson** with `lesson_id: 0` → POST /api/lessons + POST /api/units (creates both)
- Uploader never deletes modules or lessons — only creates and updates

**Position reordering** — the uploader passes `position` on every update, so Stepik will apply the new order.

---

## Title Length Limits

Stepik enforces hard character limits on titles:

| Entity | Limit |
|---|---|
| Lesson title (`lesson_title`) | **64 characters** |
| Module title (`section_title`) | **100 characters** |

Before setting any title, count its length. If it exceeds the limit:
- Shorten while preserving meaning — abbreviate technology stacks, drop filler words.
- For lesson titles starting with `STT:` / `TTS:` / `Практика:` — budget the prefix and fit the rest in the remaining chars.
- Never truncate mechanically mid-word; find a natural short form.
- If the user provides a title that is too long, propose a shortened version and wait for confirmation before saving.

## Constraints

- Keep `section_position` and lesson `position` as contiguous 1-based integers with no gaps — gaps confuse the uploader.
- Do not change `lesson_id` of an existing lesson (non-zero) — this would break the link to Stepik content.
- Do not change `section_id` of an existing module — same reason.
- Maximum 16 steps per lesson (enforced elsewhere, but mention if relevant).
- Validate JSON integrity before saving — structure.json must remain valid JSON.

---

## Workflow

1. Show the user the current structure summary.
2. Ask what needs to be changed (or proceed if the user already described the task).
3. Plan the changes and confirm with the user if the change is non-trivial (reordering multiple modules, bulk renames).
4. Apply changes to `structure.json`.
5. Show a diff-style summary of what changed.
6. Remind the user to run `upload_structure()` (or `upload_course(sync_structure=True)`) to push changes to Stepik.
