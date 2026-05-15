---
name: code-examples
description: Apply these rules when a lesson contains code that must be validated, improved, or created.
---

## Where To Store Examples

- Step-specific code examples are stored in `courses/<course>/<module>/<lesson>/code_examples/<step>/`.
- If a lesson step contains code that needs validation or rework, move it to a dedicated runnable file in that lesson-local `code_examples/<step>/` folder.
- Keep the same short index structure as in `courses/` so it is clear which course/module/lesson/step the sample belongs to.
- For lesson materials, this means numeric module and lesson folders like `03/05` and step subfolder names matching the lesson step, such as `03_text` or `02_code`.
- If an example is shared across several steps, lessons, or the whole course, store it under `courses/<course>/code_examples/`.
- Create clear local files that can be run/imported/tested separately.

## Workflow

1. Find the code fragment in the lesson HTML.
2. Decide whether it needs a separate runnable/verifiable file.
3. If needed, create the file under the appropriate `code_examples/` location.
4. Validate or improve the sample in that file.
5. Only then update the HTML fragment if required.

## Example Quality Requirements

- Keep samples compact for teaching purposes.
- Do not turn samples into full production systems if that harms clarity.
- Samples must stay technically credible and not mislead learners.
- If a sample cannot be honestly validated in the current environment, state this explicitly in the report.

## Final Check

1. Ensure the sample is in the correct `code_examples/` location.
2. Ensure path structure matches `courses/`.
3. Ensure HTML and standalone code sample are semantically aligned.
