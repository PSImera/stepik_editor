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

> The uploader uses `lesson_info.title` and `section_info.title` as "last known remote state" to decide whether to send a rename request. Editing these cache fields breaks change detection and causes the uploader to silently skip the API call.

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

Update **only** `section_title` of the target entry. Do not change `section_position` unless also reordering. Never touch `section_info` — same cache rule as for `lesson_info`.

### Renaming a Lesson

Update **only** `lesson_title` of the target entry inside its module's `lessons` array. Do not change `lesson_id` or `position` unless also reordering.

> **CRITICAL — do not touch `lesson_info.title`.**
> The uploader detects renames by comparing `lesson_title` (desired) against `lesson_info.title` (last known remote value). If you update `lesson_info.title` to match the new `lesson_title`, the uploader sees no diff and silently skips the API call — the lesson name on Stepik stays unchanged. `lesson_info` is a read-only cache; the uploader overwrites it after a successful push.

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

### Moving a Lesson to Another Module

Moving a lesson means detaching its Stepik **unit** (the link between a lesson and a section) from the old module and creating a new one in the new module. A `unit_id` is always section-specific — it cannot be reused in a different module.

**Steps:**

1. Remove the lesson entry from the old module's `lessons` array in `structure.json`.
2. Renumber remaining lessons in the old module (gap-free 1-based sequence).
3. Add the lesson entry to the new module's `lessons` array:
   ```json
   {
     "lesson_id": <existing id>,
     "lesson_title": "<title>",
     "position": <target position>,
     "lesson_info": <copy from old entry>
   }
   ```
   **Do NOT copy `unit_id` or `unit_info` from the old entry.** Leave them absent or set `"unit_id": 0`. The old unit belongs to the old module's section and is invalid in the new one.
4. Renumber lessons in the new module (gap-free 1-based sequence).
5. Run the uploader with `sync_deletions=True`:
   - The uploader will find the old unit orphaned in the source module and prompt for deletion (confirm **Y**).
   - It will create a new unit for the lesson in the destination module's section.
6. Then run `upload_course()` for both affected modules to sync steps.

> **Common mistake:** copying the full old entry including `unit_id` into the new module. The `unit_id` then points to the wrong Stepik section — the lesson appears in both modules on the site, or the unit stays in the old module while the new one is never created. Always clear `unit_id`/`unit_info` when moving.

### Removing a Lesson

1. Remove the lesson entry from the `lessons` array in `structure.json`.
2. Renumber remaining lessons so `position` stays a contiguous 1-based sequence. Re-sort the array by `position`.
3. **Delete the local lesson folder** `courses/<course>/<module>/<lesson_pos_padded>/` (e.g. `courses/voice_ai/02/04/`). Use PowerShell: `Remove-Item -Recurse -Force "<path>"`.
4. **Rename subsequent lesson folders** so their two-digit folder names match the new positions. Example: if you deleted position 4, rename `05/` → `04/`, `06/` → `05/`, etc. Use `Rename-Item`.
5. The Stepik lesson itself (`lesson_id`) is **not deleted** on the server — the uploader never deletes. The lesson becomes orphaned on Stepik and can be removed manually if needed.

### Removing a Module

1. Remove the module entry from the `structure` array in `structure.json`.
2. Renumber remaining modules so `section_position` stays a contiguous 1-based sequence. Re-sort the array by `section_position`.
3. **Delete the local module folder** `courses/<course>/<module_pos_padded>/` (e.g. `courses/voice_ai/03/`). Use `Remove-Item -Recurse -Force`.
4. **Rename subsequent module folders** to match new positions.
5. Same caveat: the Stepik section is not deleted on the server.

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
- Uploader **with default `sync_deletions=False`** never deletes — only creates and updates. With `sync_deletions=True` it interactively prompts to delete orphaned units (lessons removed from a module locally). Use `sync_deletions=True` after moving or removing a lesson.

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

## JSON Validity — Mandatory Validation Step

**After every Edit or Write to structure.json**, immediately run:

```powershell
.\.venv\Scripts\python.exe -c "import json; json.load(open('courses/<course>/structure.json', encoding='utf-8')); print('OK')"
```

If it prints anything other than `OK`, fix the JSON before proceeding. Common causes:

- **Trailing comma** — the most frequent error. Happens when removing an array element or editing a block that was not the last one: `},` before `]` or `},` before `}` at end of object. After any deletion or insertion in an array, verify the last element has no trailing comma.
- **Missing comma** — happens when inserting a new element and forgetting to add `,` after the preceding element.
- **Mismatched braces/brackets** — count `{`/`}` and `[`/`]` in the edited region.

Do not report the edit as complete until the validation command prints `OK`.

---

## Workflow

1. Show the user the current structure summary.
2. Ask what needs to be changed (or proceed if the user already described the task).
3. Plan the changes and confirm with the user if the change is non-trivial (reordering multiple modules, bulk renames).
4. Apply changes to `structure.json`.
5. Show a diff-style summary of what changed.
6. Remind the user to run `upload_structure()` (or `upload_course(sync_structure=True)`) to push changes to Stepik.
