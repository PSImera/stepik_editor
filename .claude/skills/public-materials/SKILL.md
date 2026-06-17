---
name: public-materials
description: Apply these rules whenever the task produces or edits public content.
---


## Audience And Voice

- Write for the learner directly.
- Do not expose internal author reasoning, editorial commentary, or process notes.
- Do not include behind-the-scenes explanations such as why a formulation was chosen or what learners may or may not have outside the task itself.
- Do not refer to learners in the third person inside learner-facing content.
- For explanatory narration of material already covered together earlier in the course, prefer first-person plural «мы» (author and learner together) over «вы»: write «мы уже рассмотрели, как собрать…» rather than «вы собирали…». It reads livelier and less clerical, and frames the author as working alongside the learner. Keep «вы»/the imperative for actions the learner must perform now (in practice steps): «соберите», «проверьте».
- Do not reference course modules or lessons by index number («в модуле 4», «в уроке 5.1», «в следующем модуле»). Indices shift whenever the course is restructured, and numbered cross-references read as clerical. Instead point to the material by what it covered: «когда мы собирали каскадного агента», «ранее в курсе», «в разборе российского стека». (This complements the existing rule against announcing future modules.)
- Do not re-explain basics already established earlier in the course (e.g. what distinguishes a cascade from a realtime model, what barge-in is). Reference them in one short clause and move on — assume the reader has them. Cutting this repetition is the main way to reduce filler.
- Prefer direct wording: explain what to do, what to inspect, what to submit, and what result should appear.
- Prefer a live, simple teaching voice over stiff, performative, or overly polished phrasing.
- Avoid pseudo-conversational quoted lines such as "just figure out what is happening here", "quickly understand the project", or similar theatrical inserts; state the situation directly in normal prose.
- Do not put imaginary reader reactions, imaginary inner monologue, or attributed agent speech in guillemets (ёлочки «»). For example, avoid patterns like «первая реакция: «Но у нас и так есть ветки»» or «вместо «я примерно чувствую риск»». Express the idea directly in the author's voice as normal prose.
- Avoid heavy editorial framing and abstract grand statements when a short practical sentence would do.
- Do not smooth the material into a neutral review tone if the topic depends on sharp engineering distinctions, practical tradeoffs, or strong working rules.
- Prefer a few clear, memorable operational theses over a safe but blurry explanation when that makes the method easier to reuse.
- In lessons about concrete tools and interfaces, prefer observable nouns and actions: names of screens, modes, panels, buttons, hotkeys, and menu paths are usually more useful than generalized wording about convenience or workflow "feel".

## Language And Style

- Public educational materials must be written in Russian unless the user explicitly requests another language.
- Keep wording clear, natural, and instructional; optimize for clarity over completeness.
- Prefer simple, spoken-natural style over bureaucratic, inflated, or lecture-like wording.
- Keep terminology consistent with the lesson and course.
- Prefer clearer learner-facing wording over internal jargon when the term itself is not a key concept.
- Prefer clear Russian equivalents over unnecessary English terms such as `scope`, `workflow`, `output`, or similar jargon when the concept can be expressed naturally in Russian without loss of meaning.
- For frequent engineering terms, use Russian replacements by default unless the English term itself is the subject of study: `scope` -> `границы`, `объём изменений`, or `соседние участки`; `workflow` -> `рабочий процесс` or `сценарий работы`; `output` -> `вывод` or `результат` etc. Keep the English form only where precision or interface recognizability would be lost without it.
- Do not transliterate technical terms that are not established in Russian. If a term has no settled Russian form and is normally written in English in the field, keep the English spelling rather than inventing a Cyrillic transcription: write `barge-in`, not «барж-ин»; `end-of-turn`, not «энд-оф-тёрн». A clear Russian equivalent is still preferred where one exists (`прерывание` may fit instead of `barge-in` depending on context); transliteration is the option to avoid.
- Avoid the word «зрелый» and its derivatives (зрелее, незрелый, зрелость, and similar). It carries vague quality judgment without a concrete criterion. Replace with specific observations: лучше документирован, больше примеров, шире распространён, стабильное API, and so on.
- Do not anthropomorphize code, logic, functions, modules, systems, or `legacy` in public materials. This includes dwelling metaphors and intention/emotion metaphors. Avoid wording such as `живёт`, `должна жить`, `поселить`, `любит`, `не любит`, `хочет`, `думает`, `понимает`, `вознаграждает`, or similar variants. Use direct wording such as `находится`, `расположена`, `вносится в`, `связана с`, `проходит через`, `определяется`, `зависит от`, `часто приводит к`, or `особенно рискованно в`.
- Avoid vague meta-teaching phrasing, AI filler, slogan copy, or smart-sounding paraphrase; prefer concrete wording about what the learner should do, inspect, or understand.
- Add the context required for understanding, but reduce documentation-heavy framing around tool examples when it does not strengthen the teaching point.
- Keep paragraphs and sections logically connected with natural transitions.
- Use lists only when enumeration genuinely improves comprehension. When the same point can be explained as a short connected paragraph, prefer natural prose over repeated bullet lists.
- Do not build learner-facing material out of back-to-back lists by default. If several neighboring sections turn into short bullets, rewrite part of them as connected prose so the page reads like guidance rather than a checklist dump.
- In learner-facing theory materials, avoid generic checklist blocks and headings such as "checklist", "stop-check", or similar list-shaped filler when the same idea can be explained more naturally in prose.
- Short lists are appropriate when the learner needs to compare a small set of discrete modes, options, or states. Do not ban enumeration where it genuinely lowers cognitive load.
- In practical assignments especially, prefer 1-3 short paragraphs per section and reserve lists for truly distinct items such as file sets, acceptance criteria, or submission artifacts.
- When English labels are not the subject of the material itself, prefer clear Russian equivalents or give the Russian explanation first.
- After generating or substantially rewriting public content, check the text content against /humanizer-ru patterns and fix detected issues. Apply changes to the text content only — do not touch HTML tags, attributes, or structure.

## Scope And Framing

- Keep the content focused on the actual teaching goal of the current lesson or assignment.
- Do not add meta-commentary about authoring, source checking, or recency unless that is itself the topic being taught.
- Do not start vfterial with a meta paragraph like "в этом задании вы тренируете..." or "в этом уроке вы научитесь...". Prefer entering through the actual scenario, requirement, or expected result.
- Do not widen the scope with extra features, optional extensions, or neighboring topics unless the task explicitly requires them.
- If the topic is best taught through one concrete case or one controlled comparison, prefer that structure over a broader but flatter overview.
- When a topic naturally breaks into categories, do not default to taxonomy-heavy exposition. A running example or contrastive comparison often teaches faster than a clean but abstract classification.
- If the topic is practical, try to end the explanation with a transferable form the learner can immediately reuse:
  - a prompt template;
  - a code example;
  - a rule for verification;
  - a stop-point;
  - a required output artifact.

## Illustration Placeholders

- If a screenshot is useful, for example if the object of study is a real interface state, leave a visible placeholder for the screenshot directly in the text.
- Use this exact format for screenshot placeholders: `[📷 краткое описание что показать]`. Place it as inline text at the point where the image should appear.
- Do NOT use HTML comments for image placeholders. Comments like `<!-- СКРИНШОТ ... -->` are invisible in the rendered step and must not be used.
- For a screenshot placeholder, include a short description of what exactly should be captured.
- If the object of study is the quality of an agent response, prompt, diff, or investigation result, prefer screenshots of the real run as evidence over abstract schemes.
- If the object of study is a concrete tool mechanic such as a command, status indicator, attachment flow, search mode, file picker, or rule location, prefer a screenshot.
- When the point is a process, comparison, flow, or compact abstract mechanism that a single real screen would show poorly, leave a placeholder for a diagram or scheme and create it with /shemas skill.
- Use SVG-specific rules only when the task really needs a scheme rather than a screenshot or a simple textual note.

## Formatting

- For HTML materials, preserve clean and consistent structure.
- Keep heading hierarchy consistent: `h1`, then `h2`, `h3`, and so on.
- Use `<blockquote>` for short points of emphasis or digression, such as a footnote, reference, or exception. Don't overuse it; use it sparingly.
- Mark explained terms with `<strong>`.
- Mark variables, functions, methods, classes, params, files, and technical entities with `<code>`.
- Do not place two `$` signs in the same `<td>`, `<p>`, or other inline context. Stepik runs MathJax: two `$` on the same text node turn everything between them into a formula. The HTML entity `&#36;` does NOT work — the platform converts it back to `$` on upload. The only reliable fix is to avoid two dollar signs in the same element: write price ranges as `15 / 30 долл.` or `15–30 долл.` instead of `$15 / $30`; for shell variables in `<code>`, use word form or restructure the example so no two `$` appear in the same code span.
- Format formulas in LaTeX-compatible style:
  - inline: `<span class="math-tex">\( ... \)</span>`
  - display: `<p><span class="math-tex">\[ ... \]</span></p>`
- In display formulas, use `\min\nolimits_j` when that exact style is needed.
- When prompt text is shown inside a code block in HTML, use `<code class="language-no-highlight">`.
- Do not place a line break immediately before `</code>` in code blocks.
- Do not use raw backtick characters `` ` `` in HTML content. Replace each backtick with `&#96;`. This applies to text inside `<pre><code>` blocks, `<code>` spans, questions, answer options, and task descriptions — anywhere in learner-facing content.
