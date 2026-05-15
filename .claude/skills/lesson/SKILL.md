---
name: lesson
description: Rules for editing lesson steps in `courses/`.
argument-hint: "[module] [lesson]"
---

## Purpose
- Lesson steps are public material. **Always load /public-materials and /shemas alongside this skill** — both are mandatory for any lesson generation or editing task, not optional.
- Apply these rules when the task is to generating, rewrite, improve, or update lesson HTML steps.

If `docs/<course>.md` exists for the target course, read it too.

Target: module `$ARGUMENTS` (first token = module index, second token = lesson index).
If only one token is given, treat it as the module index and ask the user for the lesson index.
If no arguments are given, ask the user for module and lesson indices.

1. Locate the lesson folder. Read `lesson.json` to get the step list (positions, types).
2. For each step in the manifest: read `{pos:02d}_{type}/task.html` for text/code/free-answer steps; question steps (`choice`, `matching`, etc.) store their text in `{pos:02d}_{type}/step.json` under the `"text"` key.
3. Check the current step count and structure.
4. Ask the user: what needs to be done with this lesson? (Create from scratch, edit specific steps, restructure, or something else.)

# Lesson Editing Rules

Rules for editing lesson steps in `courses/`.

## Lesson Structure Model

- A lesson may include theoretical steps, practical steps, or both.
- Practical assignments may also be stored separately according to the task-specific rule set and do not cancel the need to keep the lesson HTML flow coherent.
- Unless course-specific rules say otherwise, treat the default lesson body as `3-6` theory steps and add practical HTML steps only when they are pedagogically justified or explicitly requested.

## Working Approach

- First understand lesson goal, step structure, and current step position in the lesson flow.
- If previous lesson context is needed, first check summaries and use them as fast context.
- If summaries are missing or outdated, create/update them before deep rewrite of new material.
- Before generating or substantially rewriting a full lesson, identify how this lesson continues the course line rather than treating it as an isolated article.
- If user provides one or several steps, first rebuild/agree on a coherent lesson plan, then edit steps.
- If the current lesson contains a single placeholder step or an obviously incomplete structure, expand it into a proper multi-step lesson instead of preserving the placeholder layout.
- Preserve the current number of steps only when the existing lesson is already complete and pedagogically coherent, or when the user explicitly asks not to change the structure.
- Each step is edited as a separate HTML document.
- Number actions starting from one, for example `Шаг 1` instead of `Шаг 0`.

## RAG Continuity Checks

Use the `/rag` skill to avoid repeating already-covered material and to avoid pre-empting material planned for future lessons. Run these checks before writing or substantially rewriting a step — not after.

When invoking `/rag`, pass all needed arguments directly so the skill does not ask the user any questions.

### Checking what was covered before the current lesson

When authoring or rewriting a step in lesson `M/L`, invoke the `/rag` skill with:
- action: `search-history`
- course: current course
- query: the concept being introduced
- module-to: `M`, lesson-to: `L`

If a strong match (score ≥ 0.82) is found in an earlier lesson, do not re-explain from scratch — reference it briefly or build on it. Mention the earlier step to the user if relevant.

### Checking what will be covered later (when editing an earlier lesson)

When going back to edit a lesson that is not the last one in the course, invoke `/rag` with:
- action: `search`
- course: current course
- query: the concept being introduced

Filter results to those where module/lesson is greater than the current one. If a strong match is found ahead, avoid explaining the concept in full here — either introduce it lightly or omit it so the later lesson keeps its pedagogical role.

### When to skip

- Skip both checks when the task is a minor wording fix, formatting correction, or HTML structure cleanup.
- Skip if the RAG index files (`course_rag/<course>/index.faiss`, `index.pkl`) are absent — note this to the user.
- Run once per concept or once per step being substantially rewritten, not on every edit.

## Lesson Completion Actions

When you detect that lesson editing is finished — the user confirms the lesson is done, or the last step in the lesson was just edited, or test questions (тестовые задачи) were just added — **proactively offer** the following two actions. Do not execute them automatically; wait for the user's confirmation.

1. **Обновить индекс** — rebuild this lesson in the RAG index so future searches reflect the new content:
   ```
   .\.venv\Scripts\python.exe -m src.course_rag build --course <course> --module-num <M> --lesson-num <L>
   ```
2. **Сохранить саммари** — create or update the lesson summary via the `/summary` skill.

Suggest both together in one message, for example:
> Урок выглядит завершённым. Предлагаю:
> 1. Обновить RAG-индекс урока — чтобы следующие поиски учитывали новый текст.
> 2. Сохранить саммари урока.
> Выполнить оба действия?

If the user approves, run the index rebuild first, then invoke `/summary`.

## Content Requirements

### Overall Lesson Flow

- Keep narrative logical with transitions inside and between steps.
- Remove semantic repetition, including repeats between steps.
- Prefer progression-style lesson flow where later steps build on earlier ones, instead of several parallel explanations that could be read in any order.
- Do not end a step with a summary of what was just covered or with a teaser about what will happen in the next lesson.
- If the previous lesson already established a running example or a concrete investigative thread, continue it by default. If another project or case demonstrates the target skill more clearly, you may switch, but preserve continuity through the same method and make that transition explicit.
- If the previous lesson summary or agreed handoff already names a concrete artifact for the next step, treat that artifact as the default starting point for the new lesson instead of replacing it with a generic exercise.

### Theory Steps

- Do not turn lessons into large code dumps without explanation.
- If the topic is an engineering method or workflow, each theoretical step should, where possible, yield at least one concrete reusable outcome:
  - a checkable criterion;
  - a working scheme or strategy;
  - a prompt template;
  - a stop-point or handoff rule;
  - a visible completion signal.
- Do not stop at a generic explanation when the topic can be pushed into a working pattern the learner can reuse on the next task.
- When planning a multi-step lesson, make neighboring theory steps differ not only by subtopic but by their teaching function, for example:
  - why the problem appears;
  - which strategies exist;
  - how the workflow looks in tools;
  - how the result is checked or resumed;
  - how the method is practiced.
- For lessons about documentation, review, debugging, prompt quality, or answer evaluation, a comparison-driven structure is often stronger than a generic overview: weak vs strong request, broad vs narrow scope, guessed vs verified fact, early fix vs read-only check.
- If the topic naturally invites classification or taxonomy, resist turning the whole step into named categories and bullet lists. Prefer one running case, one controlled comparison, or one observable experiment that carries the explanation.
- In interface-heavy lessons, organize the step as a walkthrough of concrete screens, modes, panels, settings, or diff states rather than as a generic essay about the tool category.
- If a step introduces a new screen, panel, menu, picker, diff view, or other interface context that matters for understanding, add a screenshot or a screenshot placeholder close to the first explanation of that context.
- If one step accumulates several new interface contexts and the visuals start competing with each other, split the step or add explicit subsections so each visual anchor has one clear teaching role.
- Images for a step are stored inside its subfolder `{pos:02d}_{type}/` and named sequentially: `01.png`, `02.svg`, etc. Reference them with just the filename in `src`, for example `<img src="01.png">`.
- If a theory step explains a process, architecture, component relationships, decision flow, or comparison with no existing image, proactively create an SVG diagram using /shemas skill and embed it as an `<img>` placeholder (`src=""`, `name="01.svg"`).
- Short lists are allowed in theory when they reduce cognitive load by naming discrete modes, options, or comparisons. Avoid checklist-style list spam, but do not force dense prose where enumeration is genuinely clearer.

### Practical Steps

- In learner-facing practice, build the narration around the concrete action the learner should take now, not around commentary on what they supposedly did or did not do.
- In learner-facing practice, prefer direct Russian wording for operational actions, section titles, and UI areas. Mention the English label only secondarily, when it helps the learner find a real control in the tool interface.
- In explanations of routing or scoped rules, explicitly highlight that the goal is selective reading of only the instructions relevant to the current task.
- When a practical step continues a shared project thread, verify that its stated starting point matches the real context from the previous lesson and current project state.
- In learner-facing practice, avoid hardcoding project-specific file paths unless those paths are mandatory invariants of the course artifact. Prefer goal-based or layer-based guidance that still transfers to equivalent student projects.

## Lesson Authoring Quality Bar

- When generating or substantially rewriting a full lesson, first identify what new engineering capability this lesson adds relative to the already covered line of the module.
- Do not let a lesson turn into several loosely connected mini-articles on one topic. The steps should progress through one shared teaching arc and move the workflow forward.
- For each theoretical step, identify not only the subtopic but also the practical takeaway the learner should carry out of that step: a criterion, a strategy, a reusable pattern, a prompt shape, a stop-point, or another concrete working heuristic.

## Modernity And Technical Correctness

- Treat technical relevance as a mandatory requirement: all technologies, APIs, libraries, models, and workflows presented in the lesson must be verified for current-day relevance before editing is considered complete.
- Remove or rewrite outdated recommendations, deprecated APIs, legacy workflows, and historically common but no longer preferred practices.
- Prefer current practical techniques.
- Present up-to-date material as the normal lesson narrative, not as commentary about freshness checks or documentation review.
- Validate code examples for plausibility and internal consistency.
- Fix clearly broken examples.

## Final Check

1. Ensure only required lesson steps were changed.
2. Ensure text is not corrupted by encoding.
3. Ensure basic HTML integrity is preserved.
4. Ensure terminology and style are consistent across lesson steps.
5. Ensure edited HTML files do not end with an extra blank line.
6. If lesson was substantially updated/finalized, create or update the summary file inside that lesson folder.
7. Ensure theory steps that explain architecture, flows, or comparisons have an SVG diagram or an `<img>` placeholder (`src=""`) — not bare text or ASCII art.
8. After all steps are done, offer to rebuild the RAG index for this lesson and save the summary (see **Lesson Completion Actions**).

