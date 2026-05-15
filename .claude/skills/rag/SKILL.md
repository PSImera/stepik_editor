---
name: rag
description: Use when the user explicitly asks to search by meaning or through the index, or when local lesson files and summaries are insufficient for finding relevant prior explanations, terminology, or closely related steps inside the same course. Contains rules for semantic search using the course RAG index.
argument-hint: "[course] [build|update|search|search-history]"
---

# Argument Parsing

Parse `$ARGUMENTS` by recognising these optional tokens in any order:

| Token | Meaning |
|---|---|
| Matches a course name (see list below) | `course` |
| `build`, `update`, `search`, `search-history` | `action` |

**Known courses** — read at runtime: list all subdirectories of `courses/` (use `Glob` with pattern `courses/*/` or PowerShell `Get-ChildItem courses -Directory`). Do not hardcode course names.

After parsing, ask for any missing required values using `AskUserQuestion`:

1. **course** — if absent or unrecognised, ask with a single-select showing the list of folders inside `courses/`.
2. **action** — if absent, ask with four options:
   - **build** — собрать индекс с нуля (или пересобрать весь курс / модуль / урок)
   - **update** — обновить один шаг в существующем индексе
   - **search** — поиск по всему индексу курса
   - **search-history** — поиск только по пройденной части курса (до указанного урока)

---

# ACTION: build

Ask (if not provided in arguments):
- **scope** — что пересобрать:
  - **Весь курс** (default)
  - **Модуль** → ask free-text module number
  - **Урок** → ask free-text module + lesson number
  - **Шаг** → ask free-text module + lesson + step number

Run:

```
.\.venv\Scripts\python.exe -m src.course_rag build --course <course> [--module-num <n>] [--lesson-num <n>] [--step-num <n>]
```

After the command finishes, report `files_count` and `chunks_count` from the JSON output.

---

# ACTION: update

Ask for the step file path if not provided. The expected format is:

```
courses/<course>/<module>/<lesson>/{pos:02d}_{type}/task.html
```

Run:

```
.\.venv\Scripts\python.exe -m src.course_rag update --course <course> --file <path>
```

After the command finishes, confirm the step was updated and report its `chunk_id` prefix from the output.

---

# ACTION: search

Ask for the search query if not provided.

Optionally narrow scope — ask if the user wants to filter by module / lesson / step (default: no filter, search the whole course).

Run:

```
.\.venv\Scripts\python.exe -m src.course_rag search --course <course> --query "<query>" [--k 5] [--module <n>] [--lesson <n>] [--step <n>]
```

Present results as a numbered list: `score`, `step_title`, `section_title`, location (`module-lesson-step`), and a short excerpt of `page_content`.

---

# ACTION: search-history

Use this when authoring a lesson and you need to check what was already explained *before* the current lesson.

Ask for:
1. **query** — what to search for
2. **module-to** + **lesson-to** — the lesson being authored (boundary: everything *before* this lesson is searched)
3. **step-to** (optional) — further narrow to steps before this position

Default boundary rule: when authoring lesson `M/L`, search up to `M/(L-1)` end.

Run:

```
.\.venv\Scripts\python.exe -m src.course_rag search-history --course <course> --query "<query>" --module-to <n> --lesson-to <n> [--step-to <n>] [--k 5]
```

Present results the same way as `search`.

---

# General rules

- Course-specific vector indexes are stored under `course_rag/<course>/`.
- Treat each course index as isolated. Never search one course when the task targets another course unless the user explicitly asks for cross-course comparison.
- When authoring a new lesson step, use course RAG as a fallback context source if the relevant earlier explanations are not already present in the chat context or lesson summaries.
- For continuity checks like "have we already explained X before this lesson?", prefer `search-history` up to the previous lesson boundary instead of searching the whole course.
- If a task adds or edits a learner-facing cross-course mention, document it via the /context-links skill.
- Do not use course RAG by default for strictly local edits when the needed context is already available in the current lesson and its summaries.
- Supported index files per course:
  - `course_rag/<course>/index.faiss`
  - `course_rag/<course>/index.pkl`
  - `course_rag/<course>/metadata.json`
  - `course_rag/<course>/chunks.jsonl`
- The index covers only step types listed in `EditorConfig.rag_indexed_step_types` (default: `["text"]`). To index additional types (e.g. `free-answer`), add them to that list and rebuild.
- After substantial edits to an indexed step, run `update` if the index already exists or if the user asked to keep it current.
