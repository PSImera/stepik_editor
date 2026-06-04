---
name: context-links
description: Rules for using Course RAG as historical memory during lesson authoring and for making rare learner-facing references to other courses.
---

## Why This Exists

- While writing a new lesson, the agent may need to check whether a concept was already explained earlier in the same course.
- Reading many previous HTML files in full is slow and wastes context.
- Course RAG should therefore serve as a semantic fallback for continuity checks and for finding earlier terminology, examples, and explanations.
- In rare cases, a lesson may also benefit from a short native reference to another course. Those references should be deliberate and limited.

## Load On Demand

- This document is the rule source for two optional capabilities:
  - historical semantic search inside the current course;
  - rare learner-facing references to other courses.
- If the task only needs Course RAG, you do not need to open [links-catalog.md](../../../docs/links-catalog.md).
- Open [links-catalog.md](../../../docs/links-catalog.md) only when you actually need to add, edit, validate, or phrase a learner-facing cross-course reference.
- Treat the catalog as data, not as the place where the behavioral policy lives.

## Historical Search Inside The Current Course

- First prefer use /summary skill when they already answer the question.
- If summaries are missing or too shallow, use Course RAG on the current course.
- When writing lesson `M/L`, search only within the already covered part of the course:
  - normally up to the end of lesson `M/(L-1)` in the same module;
  - if the needed context may come from earlier modules, search from the course start up to that same boundary;
  - do not rely on future lessons as context unless the user explicitly asks for cross-checking against later material.

Recommended command:

- `.\.venv\Scripts\python.exe -m src.course_rag search-history --course <course> --query "<query>" --module-to <module> --lesson-to <lesson>`

Examples:

- Before writing `03/03`, check history through `03/02`.
- Before writing the first lesson of a module, search through the whole previous module.

## What To Use RAG For

- Checking whether concept `X` was already introduced.
- Finding the established wording for a term.
- Finding where a tool, workflow, or file artifact was already explained.
- Finding related examples worth briefly recalling instead of repeating from scratch.

## How To Use Findings In Learner-Facing Text

- Do not dump raw step paths into the lesson body.
- Use natural Russian phrasing that sounds like real pedagogy rather than internal navigation.
- It is fine to mention either the module/lesson position or the lesson title, whichever sounds more natural.
- Mention the earlier reference only when it actually reduces repetition or helps the learner orient themselves.

Good patterns:

- `Ранее мы уже касались установки Cursor в первом модуле, поэтому здесь не будем заново разбирать базовую настройку.`
- `В первом уроке этого модуля мы уже собрали базовый пайплайн, а сейчас сосредоточимся на оценке качества.`
- `Термин "payload" у нас уже появлялся в прошлом уроке, поэтому здесь сразу перейдём к тому, как он влияет на фильтрацию.`
- `С самим принципом chunking мы уже работали раньше; здесь важнее понять, как он влияет именно на retrieval quality.`

Avoid:

- `См. 03/02/01_text/task.html`
- `Как было сказано в chunk_id 03-02-01:4`
- dry references with no pedagogical role
- repeated reminders in every step

## How To Report RAG Findings To The User

- In the author-facing report, you may cite exact file paths or lesson identifiers.
- In learner-facing materials, convert those findings into natural prose.
- If RAG found several close hits, prefer the earliest or clearest one instead of stacking many references.

## Cross-Course References

- Cross-course references are optional and should be rare.
- The hard ceiling is tracked per source course and per target course in [links-catalog.md](../../../docs/links-catalog.md).
- For any given source course, at most two outbound mentions are allowed to any one target course.
- Only reference a different course when it genuinely helps the learner:
  - a deeper specialized track;
  - a neighboring practical specialization;
  - a topic intentionally out of scope for the current course.
- Never advertise the same course from inside itself.
- If a cross-course reference is used, prefer a brief native sentence, not a banner-like sales insert.
- Before adding a new cross-course mention, check the source course ledger in [links-catalog.md](../../../docs/links-catalog.md).
- After adding a new cross-course mention, update the ledger in [links-catalog.md](../../../docs/links-catalog.md) in the same task.

Good patterns:

- `Если хочется глубже уйти именно в production RAG, это уже отдельная большая тема; для неё у нас есть отдельный курс RAG Engineer PRO.`
- `Тему A/B-тестов здесь затрагивать подробно не будем: она лучше раскрывается в отдельном курсе по экспериментам и анализу данных.`

Avoid:

- hard sell language inside ordinary theory
- multiple promotional links in one lesson
- inserting cross-course promotion when it does not help the current explanation

## Source Of Cross-Course Links

- Use [links-catalog.md](../../../docs/links-catalog.md) as the source of truth for external course references and promo links.
- Treat the ledger in that file as authoritative for whether a new mention is still allowed from the current course to the target course.
- Do not open the catalog by default just because this file was opened; open it only when the current task actually needs a cross-course link or ledger check.
- When a learner-facing text needs a cross-course mention, choose one relevant course from that catalog and use either:
  - a plain referral link;
  - a discounted promo link, if the user explicitly wants course-internal promotion.
- When choosing a discounted promo link, prefer a field named `discount_link_<percent>` from the catalog.
- Interpret `<percent>` in `discount_link_<percent>` as the authoritative discount size and use that same number in learner-facing wording, for example `со скидкой 25%`.
- If the catalog entry only has the generic field `discount_link`, you may use that URL as a discount link only when needed, but do not state any discount size in the lesson text.
- If the catalog lacks a confident course description, rely on the title and a conservative one-line explanation aligned with the course name rather than inventing details.
