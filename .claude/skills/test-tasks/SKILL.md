---
name: test-tasks
description: Rules for generating тестовые задачи (test tasks) for lessons.
argument-hint: "[module] [lesson]"
---

Target: module `$ARGUMENTS` (first token = module index, second token = lesson index).
If only one token is given, treat it as the module index and ask the user for the lesson index.
If no arguments are given, ask the user for module and lesson indices.

1. Locate the lesson folder. Read `lesson.json` to get current step list (positions and types).
2. Read theory steps: `{pos:02d}_text/task.html` for each text step in the manifest.
3. Check whether тестовые задачи step subfolders already exist in this lesson.
   - Exist → ask the user: update existing test tasks or add new ones?
   - Do not exist → confirm with the user that lesson theory is finalized, then generate test tasks.


## Purpose

- Apply these rules when the user asks to prepare тестовые задачи for already approved lesson theory.
- By default, generate test tasks only after the user accepts the final lesson theory.
- These test tasks are public material. **Always apply /public-materials skill** — it is mandatory, not a suggestion.

## Source Of Truth

- This file is the authoritative source for test task format and validation.
- If existing test task step folders in the repository use a different or older format, do not copy that format unless the user explicitly asks to preserve it.

## Where To Store Test Tasks

- Each тестовая задача occupies its own step subfolder inside the lesson folder: `{pos:02d}_{type}/step.json`.
- The position comes from the manifest: test tasks follow theory steps and continue the lesson step numbering.
- Supported test task types: `choice`, `sorting`, `matching`, `fill-blanks`, `number`, `string`, `math`, `table`.
- After creating test task files, update `lesson.json` to add each new step entry.

### lesson.json entry for a new test task step

```json
{"position": 5, "step_source_id": null, "type": "choice", "cost": 0}
```

`step_source_id` is `null` for steps not yet uploaded to Stepik.

## Test Task File Format

Each test task is stored as `step.json` in its subfolder. The `"text"` key always comes first and contains the task HTML. All other fields mirror the Stepik API `block.source` structure.

### Fields common to all task types

- `"text"` — the question/task statement. Always HTML; always wrapped in `<p>`. Use `<code>` for inline code, not backticks.
- `"feedback_correct"` — comment shown to the learner after a correct submission. Displayed above the options. Leave `""` if not needed.
- `"feedback_wrong"` — comment shown after an incorrect submission. Use to give a hint or point to the relevant theory. Leave `""` if not needed.

### Choice (single or multiple correct answers)

```json
{
  "text": "<p>Question text?</p>",
  "is_multiple_choice": false,
  "preserve_order": false,
  "sample_size": 4,
  "is_html_enabled": true,
  "is_options_feedback": false,
  "options": [
    {"is_correct": false, "text": "Wrong option 1", "feedback": ""},
    {"is_correct": true,  "text": "Correct option",  "feedback": ""},
    {"is_correct": false, "text": "Wrong option 2", "feedback": ""},
    {"is_correct": false, "text": "Wrong option 3", "feedback": ""}
  ],
  "feedback_correct": "",
  "feedback_wrong": ""
}
```

**Key fields:**
- `is_multiple_choice` — `true` for multiple correct answers.
- `sample_size` — how many options the learner sees per attempt. If less than total options, Stepik randomly picks a subset. **Do not use `is_multiple_choice: true` together with a limited `sample_size`** — a learner may see only one correct answer while the task says "select answers", which is confusing.
- `preserve_order` — `true` to keep options in a fixed order (not shuffled).
- `is_options_feedback` — `true` to show per-option feedback. Per-option `feedback` is shown when the option was incorrect and the learner selected it, OR when the option was correct and the learner did NOT select it.
- `feedback_correct` / `feedback_wrong` — general comment shown above all options after submission.
- Images cannot be embedded in options — if visuals are needed, number them in the theory step and reference by number in the option text.

### Sorting

```json
{
  "text": "<p>Arrange the steps in the correct order</p>",
  "is_html_enabled": false,
  "options": [
    {"text": "First step (correct position 1)"},
    {"text": "Second step (correct position 2)"},
    {"text": "Third step (correct position 3)"},
    {"text": "Fourth step (correct position 4)"}
  ],
  "feedback_correct": "",
  "feedback_wrong": ""
}
```

**Key fields:**
- `options` — items listed in the **correct** order. Stepik shuffles them for the learner; the learner must restore this order.
- `is_html_enabled` — `true` to allow HTML markup inside option text.
- Always state the sorting criterion explicitly in the task text (alphabetical, chronological, by priority, etc.).
- Use for sequences that have a single unambiguous correct order: execution steps, historical events, pipeline stages.
- Do not use when the correct order could reasonably vary or be argued — that causes learner frustration.

### Matching

```json
{
  "text": "<p>Match the terms to their descriptions</p>",
  "is_html_enabled": true,
  "preserve_firsts_order": true,
  "pairs": [
    {"first": "Term A", "second": "Definition A"},
    {"first": "Term B", "second": "Definition B"},
    {"first": "Term C", "second": "Definition C"},
    {"first": "Term D", "second": "Definition D"}
  ],
  "feedback_correct": "",
  "feedback_wrong": ""
}
```

**Key fields:**
- `preserve_firsts_order` — `true` to fix the order of the left column. The right column is always shuffled regardless.
- `pairs` — left column is `first`, right column is `second`. Both columns can contain plain text or HTML (if `is_html_enabled` is set on the step).
- Pairs can be asymmetric: a left item may be matched to an empty right side — use this for "which of these belong to category X" type tasks without forcing a one-to-one pairing.
- Always specify the sort order or matching criterion explicitly in the task text.

### Fill Blanks

```json
{
  "text": "<p>Complete the statement</p>",
  "is_case_sensitive": false,
  "is_detailed_feedback": false,
  "is_partially_correct": false,
  "components": [
    {"type": "text", "text": "The command to install packages is "},
    {"type": "input", "options": ["pip install", "pip i"], "feedback": ""},
    {"type": "text", "text": "."}
  ],
  "feedback_correct": "",
  "feedback_wrong": ""
}
```

**Key fields:**
- `components` alternates `"type": "text"` (static text) and `"type": "input"` (blank). A blank has `options` — a list of accepted answers.
- `is_case_sensitive` — applies to all blanks.
- `is_partially_correct` — `true` to award partial credit when only some blanks are filled correctly.

### Number

```json
{
  "text": "<p>What is the result of 2 + 2?</p>",
  "options": [
    {"answer": "4", "max_error": "0"}
  ],
  "feedback_correct": "",
  "feedback_wrong": ""
}
```

**Key fields:**
- `answer` — the correct numeric value as a string.
- `max_error` — allowed tolerance. Use `"0"` for exact integer answers; use e.g. `"0.01"` for floating-point.
- Good for tasks where the learner must compute a result rather than pick from options.

### String

```json
{
  "text": "<p>Enter the Python keyword used to define a function</p>",
  "pattern": "def",
  "use_re": false,
  "match_substring": false,
  "case_sensitive": false,
  "code": "",
  "is_text_disabled": false,
  "is_file_disabled": true,
  "feedback_correct": "",
  "feedback_wrong": ""
}
```

**Key fields:**
- `pattern` — the correct string or regex pattern.
- `use_re` — `true` to treat `pattern` as a regular expression.
- `match_substring` — `true` to accept the pattern anywhere in the answer, not only as a full match.
- `case_sensitive` — `false` by default.
- Use for short free-text answers: a command, a keyword, a file name. Avoid for anything the learner might phrase in many valid ways.

### Math

```json
{
  "text": "<p>Solve: $x^2 = 4$, $x > 0$</p>",
  "answer": "2",
  "numerical_test": {
    "z_re_from": "-10",
    "z_re_to": "10",
    "z_im_from": "0",
    "z_im_to": "0",
    "z_re_steps": 5,
    "z_im_steps": 1
  },
  "feedback_correct": "",
  "feedback_wrong": ""
}
```

**Key fields:**
- `answer` — a mathematical expression. Supports LaTeX-style math and symbolic variables.
- `numerical_test` — defines numeric sampling range used to verify the symbolic answer. `z_re_from`/`z_re_to` bound the real axis; `z_im_*` bound the imaginary axis (keep at `"0"` for purely real problems).
- Use when the learner must express a formula or symbolic result, not just a number.

### Table

```json
{
  "text": "<p>Mark which frameworks are frontend</p>",
  "columns": [
    {"name": "Yes", "choice_type": "radio"},
    {"name": "No",  "choice_type": "radio"}
  ],
  "rows": [
    {"name": "React",   "columns": [true,  false]},
    {"name": "Django",  "columns": [false, true]},
    {"name": "Vue",     "columns": [true,  false]},
    {"name": "FastAPI", "columns": [false, true]}
  ],
  "options": {},
  "description": "",
  "is_always_correct": false,
  "feedback_correct": "",
  "feedback_wrong": ""
}
```

**Key fields:**
- `columns[].choice_type` — `"radio"` means one selection per row (toggle buttons); `"checkbox"` means multiple selections per row (checkboxes).
- `rows[].columns` — boolean array matching the column order; `true` marks a correct cell.
- `options` may contain `{"shuffle_rows": true, "shuffle_columns": true}` to randomize order.
- Good for classification tasks: rows are items, columns are categories. Each row becomes an independent multiple-choice or single-choice mini-task.

## Test Content

- **Target: 10 test tasks per lesson.** Do not deviate from this without explicit user instruction.
- Reducing the count is only allowed when 10 high-quality tasks cannot be produced — meaning tasks that are simultaneously: non-trivial (answer is not obvious without understanding the topic), non-duplicating (each task covers distinct knowledge), and grounded in the lesson theory. If this threshold cannot be met, explain the reason to the user and state how many quality tasks were produced and why.
- Never reduce the count silently: if generating fewer than 10, always state the reason explicitly.
- In a standard set of 10 tasks, include a mix of types: single correct answer (`choice`), multiple correct answers (`choice` with `is_multiple_choice: true`), and `matching`.
- Do not make a lesson consist entirely of `choice` tasks — it gets boring and learners can brute-force with unlimited attempts. Mix in `matching` and other types.
- The number of tasks of each type should depend on how well that type reflects the lesson theory, not on an obligation to use every type.
- The order of tasks should follow the lesson theory. Start with tasks about the first step, then the second, and so on.
- Do not split tasks into groups by type.

## Task Text Requirements

- Task text (`"text"` field) must always be wrapped in a `<p>` tag. Use `<code>` for inline code references. Do not use backticks — Stepik does not render them.
- Answer options (`options[].text`, `pairs[].first`, `pairs[].second`) are **plain text by default**. HTML in options is only allowed when `is_html_enabled: true` is set on the step; use it sparingly.
- Images cannot appear inside test task options. If a visual is needed, place it in a preceding theory step, number it, and reference the number in the task text.

## General Requirements

- Generate HIGH-QUALITY test tasks.
- Task quality is defined primarily by the answer NOT BEING OBVIOUS.
- Avoid trivial or overly obvious tasks.
- Avoid duplicate checks of the same knowledge.
- Wording must be clear, natural, and technically precise.
- Tasks must test understanding of theory, not memorization of random code details.
- Each task must be solvable based on the lesson theory and/or lesson entities.
- **Do not use practice steps as task material.** Steps with a «Практика:» heading, project-specific examples from those steps, and expected task outcomes are off-limits for test tasks.
- **Do not test lesson-specific task outcomes.** Tasks must check understanding of general principles and theory, not actions or deliverables defined in any specific practice step of this lesson.

## Task Type Rules

### Tasks With One Correct Answer

- Provide 4 answer options in `options`.
- Place the correct option at index 1 (second in the array, position 2 for the learner).
- Keep each option text within 60 characters.
- The correct option MUST NOT BE LONGER than all incorrect options.
- At least one incorrect option MUST BE STRICTLY LONGER than the correct one.
- Before finalizing, verify all checks above for each single-answer task. Count characters explicitly if needed.

### Tasks With Multiple Correct Answers

- Set `"is_multiple_choice": true`.
- Mark each correct option with `"is_correct": true`.
- Do NOT set a limited `sample_size` on multiple-correct-answer tasks — a learner may see fewer correct options than exist, making the task unsolvable as stated.
- Make sure the tasks test conceptual understanding rather than wording tricks.

### Matching Tasks

- Use 4 pairs unless the user requests otherwise.
- Do not overcomplicate them; matching tasks should test understanding of structure, roles, differences, or cause-and-effect relationships.
- Always state the matching criterion explicitly in the task text (e.g. "Match each tool to its purpose").

### Sorting Tasks

- List items in `options` in the correct order — Stepik shuffles them automatically.
- Use only when there is a single unambiguous correct order.
- State the criterion (e.g. "in order of execution", "from general to specific") in the task text.
- 4–6 items is the comfortable range; more than 6 becomes tedious to drag.

### Table Tasks

- Use `"radio"` columns when exactly one answer is correct per row; use `"checkbox"` when multiple are valid.
- Keep the number of rows to 4–6 for readability.
- Make sure the classification criterion is stated clearly in the task text.

## Final Check

- Always perform a separate review step after generation.
- Make sure the tasks are based on the final lesson theory.
- For single-answer tasks, check: exactly 4 options; correct answer at index 1; each option within 60 characters; correct answer not longer than all incorrect options; at least one incorrect option strictly longer.
- For multiple-answer tasks, check that `sample_size` equals the total number of options (no truncation).
- Make sure `lesson.json` is updated with all new test task step entries.
- Make sure subfolder names match the step type: `{pos:02d}_choice`, `{pos:02d}_matching`, etc.
- Make sure test task steps continue the lesson step numbering after theory steps.
