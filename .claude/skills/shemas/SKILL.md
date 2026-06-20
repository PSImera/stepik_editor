---
name: shemas
description: Apply when a lesson step needs a visual diagram, architecture scheme, or
  explanatory flow; when the user says "добавь визуал", "нужна схема", "сделай диаграмму", "покажи визуально",
  "нужно визуально продемонстрировать", "хочется больше визуала"; or proactively
  during lesson authoring when a theory step explains a process, architecture, classification,
  or comparison that would be clearer as a diagram.
  Do not use for ordinary screenshots or generic image placement.
when_to_use: "Trigger: 'добавь схему', 'нужен визуал', 'сделай диаграмму', 'покажи
  архитектуру', 'нужно показать наглядно', 'add a visual', 'create a diagram',
  'show this visually'. Also trigger automatically during lesson editing when a theory
  step covers architecture, flows, classifications, or comparisons with no existing image."
---

## Purpose

- Apply when a lesson step contains a placeholder or a request for a visual that can be expressed as an SVG scheme.
- Apply **proactively during lesson authoring**: when a theory step explains a process, architecture, component relationships, decision flow, or comparison that a diagram would make clearer, create the SVG without waiting for an explicit user request.
- Do not use this document for ordinary screenshots, photo-style illustrations, or generic image placement.
- Use these rules together with /public-materials skill and the task-specific document selected from `AGENTS.md`.

## Placeholder And Embedding Workflow

- **Planning stage (SVG not yet created):** insert a visible text placeholder in the lesson HTML at the position where the image should appear:
  `<p>📸 [Диаграмма: краткое описание — файл 01.svg]</p>`
- **SVG created locally (not yet uploaded to Stepik):** replace the text placeholder with an `<img>` tag that has the correct `name` attribute and an empty `src`:
  `<p><img alt="описание диаграммы" height="H" name="01.svg" src="" width="680"></p>`
  This is the visible "pending upload" placeholder in the Stepik editor.
- **SVG uploaded:** the `src` attribute gets the Stepik CDN URL; width/height are updated to match the actual rendered size.
- Never leave ASCII art in a lesson HTML as the final visual output; always replace it with a proper SVG.

## When To Use SVG Schemes

- Use SVG only when the material needs a compact explanatory scheme, process diagram, architecture sketch, flow, or visual comparison.
- If a screenshot would communicate the point more directly, prefer a screenshot placeholder instead of an SVG scheme.
- If a diagram is useful but not yet being drawn in the current task, leave a placeholder in the lesson text and create the SVG file only when requested.

## Placeholder In Lesson Text

- For a diagram placeholder, describe what should be shown in the scheme.
- Use a visible placeholder in this format: `📸 [Диаграмма: краткое описание содержания — файл 01.svg]`.
- The placeholder should help the editor understand what entities, arrows, states, or comparisons must appear in the scheme.

## File And Embedding Expectations

- Save the scheme as a separate `.svg` file.
- When the scheme is generated from Mermaid, save the editable source `.mmd` file next to the final `.svg`.
- Keep the SVG self-contained: do not rely on external CSS, variables, fonts, or assets when they are not strictly required.
- Follow the project image placement and filename rules from `AGENTS.md` for the target lesson and step.
- If the lesson primarily teaches a real interface screen, panel, or settings area, do not replace that screenshot with an SVG scheme. Use SVG only when it explains the idea more directly than a real screen would.

## SVG Canvas And Structure

- Use `viewBox="0 0 680 H"` and `width="100%"` as the default responsive canvas pattern.
- Define reusable styling inside `<defs><style>...</style></defs>`.
- Declare arrow markers inside `<defs>` when arrows are used.
- Do not add comments inside the SVG code.

## Styling Rules

- Include all used CSS classes directly inside the SVG file.
- Use the following base classes when they fit the diagram:

```css
.c-gray rect  { fill: #f3f4f6; stroke: #d1d5db; }
.c-teal rect  { fill: #ccfbf1; stroke: #14b8a6; }
.c-coral rect { fill: #ffe4e6; stroke: #f43f5e; }
.c-purple rect{ fill: #ede9fe; stroke: #8b5cf6; }
.ts  { fill: #111827; font-family: Arial, sans-serif; }
.arr { stroke: #444441; stroke-width: 1.2; }
```

- Use `.ts` for text inside blocks and headings inside the scheme.
- Do not duplicate the text `fill` color in element attributes when `.ts` already defines it.
- For text outside blocks, such as axis labels or short explanatory captions, set visual attributes directly on the element, for example `font-size="12"` and `fill="#444441"`.
- Draw arrows with `class="arr"` and `marker-end="url(#arrow)"`.
- For diagram blocks, use `rx="6"`.
- Do not set `stroke-width` inline on blocks when it is already defined in CSS.

## Visual Constraints

- Avoid gradients, shadows, and decorative effects.
- Prefer a clean flat style that stays readable inside lesson pages.
- Keep the diagram compact and instructional rather than ornamental.

## Text Minimalism

- Put the **necessary minimum** of text on a scheme: block labels, short captions, arrow labels, and nothing more.
- A scheme is not a place to repeat the lesson. Do **not** copy paragraphs, explanations, definitions, or sentences from the lesson text into the diagram — the surrounding HTML already carries that context.
- Labels should be short noun phrases or single keywords, not full sentences. If a block needs a sentence to be understood, the wording is too long — shorten it or move the explanation back into the lesson text.
- The reader should grasp the structure from the visual layout (blocks, arrows, grouping); the words only name the parts. When in doubt, cut text rather than add it.

## Course-Observed Style Baseline

- Before drawing a new scheme, inspect `2-4` existing SVG files from the current course and inherit their dominant palette, density, and text rhythm instead of inventing a new visual language.
- If the current task or a course-specific rule file names a preferred reference diagram, use it. Otherwise, infer the local visual baseline from several existing SVG files in the same course.
- In this repository, the dominant baseline is usually:
  - compact canvas, often around `680px` wide;
  - flat cards or lanes with soft fills and thin borders;
  - rounded corners on cards and panels, typically around `rx="6"`;
  - `Arial, sans-serif`;
  - short labels, usually `1-2` short lines inside a block;
  - restrained emphasis: bold is acceptable for short headings, but not for every line inside the scheme;
  - text should feel light and readable rather than visually heavy; avoid oversized font sizes, repeated bolding, and dense multi-line copy;
  - alignment on a visible grid with even spacing between blocks;
  - color applied to the whole block, not to small decorative side markers.
- If text starts overflowing, shorten the wording first. Do not compensate with oversized cards or dense multi-line paragraphs.
- Prefer one teaching point per diagram. If the scheme starts behaving like a slide full of prose, simplify or split it.
- In comparison-style schemes, prefer calm panels with evenly stacked rows over crowded graph-like layouts.

## Mermaid Workflow

- Use Mermaid only when it is genuinely the right tool for the structure: flow, route, sequence, state change, decision path, or another graph-like diagram that benefits from text-first authoring.
- Do not use Mermaid by default for infographics, comparison panels, editorial cards, matrices, stacked teaching rows, or other layouts where composition matters more than graph structure.
- If the lesson needs a tightly controlled comparison card or infographic composition, create the final diagram directly as SVG.
- When Mermaid is used in this repository:
  - keep the editable source as `.mmd` next to the exported `.svg`;
  - render through the project toolchain, not through ad-hoc website exports;
  - use the project config in `.claude/skills/shemas/tools/stepik_mermaid_config.json`;
  - use the wrapper command `powershell -ExecutionPolicy Bypass -File .\.claude\skills\shemas\tools\render_mermaid.ps1 -InputFile <path-to.mmd> [-OutputFile <path-to.svg>]`.
- Treat the Mermaid config as a constrained style layer for graph-like schemes only. It should stay close to the course look:
  - rounded corners around `6px`;
  - `Arial, sans-serif`;
  - light readable text rather than heavy bold text;
  - calm fills and thin borders close to the dominant local card-based SVG style of the current course;
  - no decorative gradients, shadows, or flashy accents in the final look.
- Keep Mermaid node text short and concrete. If a node needs more than `2-3` short lines, the wording is usually too long for the house style.
- Prefer neutral flowchart layouts with predictable spacing over decorative Mermaid features.
- If Mermaid cannot reproduce the needed editorial structure cleanly, switch to hand-authored SVG instead of forcing the diagram into an awkward Mermaid layout.

## Authoring Workflow

- For each new diagram, follow this sequence:
  1. Read the lesson step and identify the single teaching point the diagram should explain.
  2. Inspect `2-4` existing SVG files from the same course, including any especially relevant local reference explicitly named by the task or by a course-specific rule file.
  3. Decide whether the diagram is graph-like enough for Mermaid. If it is really an infographic or editorial comparison, choose hand-authored SVG immediately.
  4. Write a short diagram brief for yourself: entities, rows or blocks, arrows if any, and the exact comparison or process being taught.
  5. Keep labels short before rendering; shorten text first instead of planning oversized boxes.
  6. If using Mermaid, save the source as `.mmd` next to the target `.svg` and render it through `.claude/skills/shemas/tools/render_mermaid.ps1`.
  7. Inspect the generated result visually or by reading the SVG structure for overflow, excessive visual weight, missing rounded corners, or broken alignment.
  8. If the output still looks too heavy or structurally wrong, either simplify the Mermaid source or switch to hand-authored SVG.
