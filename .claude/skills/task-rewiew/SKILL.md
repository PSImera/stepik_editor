---
name: task-rewiew
description: Rules for creating practical assignments that are reviewed by people.
---

## Purpose

- Apply these rules when the user asks to create a practical assignment that will be reviewed by other students or by a teacher.
- This is public learner-facing content. **Always use /public-materials skill** together with these rules — it is mandatory, not optional.
- Use the lesson theory as the source of the task topic, scope, and expected difficulty.
- Keep the assignment focused on one lesson within one module and one course.

## Where To Store Review Tasks

- A review task is a `free-answer` type step. Store it as `{pos:02d}_free_answer/task.html` inside the lesson folder.
- If peer or instructor review criteria (rubrics) are needed, also create `{pos:02d}_free_answer/instruction.json` with the review settings.
- Add the step entry to `lesson.json`: `{"position": <pos>, "step_source_id": null, "type": "free-answer", "cost": 1, "instruction_type": "peer"|"instructor", ...}`.

## Review Type Requirement

- The request must explicitly state how the result will be reviewed:
  - by other students;
  - by a teacher only.
- If the user did not specify the review type, the agent must ask a clarifying question before creating the assignment.
- At the end of the assignment, explicitly state which review mode is used.

## Content Requirements

- This is a description of a practical assignment intended for the student.
- The assignment must clearly describe what the student needs to do and what to submit for review.
- The assignment must be based on the lesson material and reinforce the main idea of that lesson.

## Allowed Submission Formats

- The result of the assignment may be:
  - plain text;
  - a link, for example to a GitHub repository;
  - an attached image or screenshot;
  - a combination of the above.
- Therefore, the assignment must ask the student to submit one of these options.
- Prefer asking for a concrete artifact with visible structure rather than a vague "try it" or "think about the method."
- In the submission section, list the required elements of the answer directly and unambiguously. Do not use wording like `if available` for something that is actually required.
- If the result must be in a repository, do not ask the student to duplicate the same result in the answer field; a link to the repository is enough, and it does not need to be duplicated in the answer field.

## Task Design Requirements

- Create a practical assignment based on the lesson materials.
- The assignment may ask the student to write text, demonstrate a result, configure a tool, or publish code externally if that matches the lesson.
- The assignment must remain understandable.
- Keep terminology consistent with the lesson.
- Do not require knowledge that was not taught in this lesson or in previous lessons of the course unless the user explicitly asks to add it.
- If the assignment may have several correct outcomes, describe the valid result options in advance instead of building only one scenario into the task statement.

## instruction.json Defaults

When creating `instruction.json` for a peer-reviewed step, use these defaults unless the user specifies otherwise:

```json
{
  "strategy_type": "peer",
  "min_reviews": 3,
  "text": "",
  "rubrics": [
    {
      "text": "<p>Зачет / Не зачет</p>\n",
      "cost": 1,
      "position": 1
    }
  ]
}
```

- `min_reviews: 3` — three peer reviews required by default.
- The user may request different rubrics, more criteria, or a different `min_reviews` value — apply those instead.
- For `instruction_type: "instructor"` steps, an `instruction.json` is not required.

### Rubric count and scoring

- A single rubric with `cost: 1` and text "Зачет / Не зачет" is the default only for simple, single-part tasks.
- If the assignment has multiple clearly separable parts (different briefs, different scenarios, different deliverables), create one rubric per part. This makes it possible for a reviewer to award partial credit rather than all-or-nothing.
- Rubric `cost` reflects the difficulty and weight of that part:
  - Simple or mechanical checks → `cost: 1`.
  - Parts that require analysis, synthesis, or produce a larger artifact → `cost: 2` or more.
- Write descriptive rubric `text` instead of "Зачет / Не зачет": state what specifically must be present for a pass, and what does not count (e.g. "общая фраза без критерия — не зачёт").
- Always ask reviewers to leave a short comment explaining each score — add this to the `text` field of `instruction.json`, not to individual rubric texts.
- The `cost` field for the step in `lesson.json` must equal the **sum of all rubric costs**. Update it whenever rubrics change.

Example for a two-part task:
```json
"rubrics": [
  { "text": "<p><strong>Часть A.</strong> …</p>", "cost": 1, "position": 1 },
  { "text": "<p><strong>Часть B.</strong> …</p>", "cost": 2, "position": 2 }
]
```
→ set `"cost": 3` for this step in `lesson.json`.

### Generating the `text` field

The `text` field ("Как оценивать решение") must always be generated — never left as `""`. Generate it based on the review criteria from `task.html`.

**Important context for the author (do not expose this in the generated text):** The `text` field is shown to the student only *after* they have submitted their own answer. The student who submitted has not yet seen anyone else's work. Use this knowledge to decide *what* to write, but never write a sentence explaining *when* this text appears — that is meta-commentary and violates `/public-materials` rules.

- **Peer review**: The reviewer is another student who may not have fully understood the task. Therefore:
  - Stepik shows this field to reviewers under the heading "Как оценивать решение?" with prompts: "На что нужно обратить внимание в первую очередь?", "Что может помочь при рецензировании?", "Как выглядит идеальное решение и почему оно правильное?" — use these as the guiding questions when composing the text.
  - Frame the content as review instructions: what to check, what to look for, what an ideal answer looks like. Not a raw answer key, but guidance that helps the reviewer judge someone else's work.
  - Include the key expected findings so the reviewer can verify the work even if they struggled with the assignment themselves. Where exact wording may vary, say so — "аналогичные по сути — засчитывается."
  - Open with "Откройте репозиторий и перейдите к хэшу коммита." if the task uses a repo + commit.
  - Use `<p>` and `<ul>`/`<ol>` tags; keep it actionable and specific — no general phrases.
  - Do **not** start with phrases like "Этот текст виден только после того, как вы сдали работу" — this is a meta-comment that must not appear in student-facing content.

- **Instructor review**: The reviewer is a subject-matter expert who does not need pedagogical scaffolding. Write a dry, compact checklist or scoring guide:
  - Mirror the points or rubric structure from `task.html`.
  - State conditions for pass / partial / fail per criterion concisely.
  - No need for explanations or hints — just what to check and what counts.
  - Prose or bullet points are both fine; brevity is preferred.

After generating `instruction.json`, verify that `text` is non-empty before saving.

## Ongoing Project Assignments

- It is acceptable to combine several assignments into a certain sequence or into work on one project within a course, module, or lesson.
- If the assignments involve work on an ongoing project in a single GitHub repository, the required result should include not only a link to the repository but also the specific commit hash related to the stage of the particular assignment.
- If the reviewer needs to see the state of the work at a specific stage, build separate checkpoints or commits into the assignment for key stages and ask for exactly those links or identifiers in the submission so the required repository state can be opened.
- If the practice consists of several related steps in one repository, explicitly state the continuity between the steps: what exactly carries over from the previous step and in what context the student continues the work.
