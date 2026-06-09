---
name: fact-check
description: Thorough source-verified fact-check of a lesson. Launches parallel web-search agents per topic cluster, returns a prioritized report, then fixes all confirmed errors.
argument-hint: "[module] [lesson]"
---

## Purpose

Verify every falsifiable claim in a lesson against official sources (platform docs, GitHub repos, official product pages). Covers API endpoints, class and method names, SDK signatures, protocol types, version numbers, performance specs, and technical constraints.

This skill does NOT review style or pedagogy — only factual correctness and currency as of the current date.

## Step 1 — Locate the lesson

Parse `$ARGUMENTS` as `<module> <lesson>` (e.g. `2 1`).
If arguments are missing or ambiguous, ask the user for module and lesson indices before proceeding.

Read `lesson.json` and all text steps (`task.html`) for that lesson. Also read every code artifact that ships with the lesson — `<pre><code>` blocks inside `task.html` AND the standalone files under `code_examples/<step>/`. Code examples are the highest-value target: verify them line by line against the current official source, not just the prose around them.

## Step 2 — Extract verifiable claims

Go through each step and collect every claim that can be confirmed or refuted against an external source:

- API endpoint URLs, ports, and protocol types (REST, gRPC, WebSocket)
- Model names and version numbers
- SDK class names, method signatures, parameter names and their accepted values
- Authentication method names, header names, credential scopes, token lifetimes
- Hardware requirements (VRAM, RAM, CPU tier)
- Performance numbers (latency, speedup ratios, throughput, real-time factors)
- Library names and their claimed built-in capabilities
- Language or locale support claims
- Deployment option claims (e.g. "on-premise with identical API interface")
- Deprecation status of any tool, API version, or model mentioned

Group claims by the service, library, or technology they belong to. Each group becomes one search agent.

### Code examples — verify against the official source

For every code snippet, treat each of the following as a separate falsifiable claim and check it against the **current** docs or repository source (not the model's memory — SDKs rename things between versions):

- import paths and module layout (e.g. `pipecat.services.deepgram.stt` vs an older `pipecat.services.deepgram`);
- class and function names (renamed/aliased classes are a common trap);
- constructor and method signatures, including **exact parameter names and nesting** (e.g. `enable_metrics=True` passed directly vs wrapped in a `params=PipelineParams(...)` object);
- whether a parameter or class is **deprecated** in the current version even if it still works (note it, prefer the recommended replacement);
- credential handling (hardcoded literal keys vs reading from environment) — flag insecure or misleading patterns;
- CLI commands, package names, and install extras.

When unsure whether a symbol exists or what its signature is, fetch the actual source file / API reference, not a third-party tutorial.

### Gaps, not just errors

Beyond confirming/refuting claims, look for **gaps**: places where the material is factually correct but omits something current or important that would make it materially better. Examples: a required step the minimal example silently skips, a newer recommended API path, a security caveat (env-var keys), a renamed primary class worth one sentence of currency context. Collect these as `📌 GAP` items and report them alongside the errors — the user explicitly wants relevant additions surfaced, not only mistakes. Keep each gap scoped: an addition must earn its place, not bloat a deliberately minimal example.

## Step 3 — Launch parallel search agents

For each group, launch an Agent with `run_in_background: true`.

Each agent prompt must:
1. List each specific claim to verify as a numbered list.
2. Identify the primary official source for that technology (official docs site, GitHub repo, official changelog).
3. Instruct the agent to return each claim as: `CONFIRMED`, `INCORRECT — correct value: <...>`, or `NOT FOUND`.
4. Instruct the agent to prefer official documentation, GitHub source files (proto definitions, README, source code), and official product pages over third-party articles or community Q&A.
5. Include the current date so the agent can assess whether the information is up to date.

Do **not** wait for all agents to complete before showing partial results — report each cluster as it arrives.

## Step 4 — Compile the report

Once all agents complete, produce a single fact-check report:

```
## Факт-чек урока [M]-[L] — [Lesson title]

### [Group name]
✅ [claim] — подтверждено
❌ [claim] — НЕВЕРНО: [correct value]
⚠️ [claim] — не найдено / требует уточнения
📌 [gap] — корректно, но стоит дополнить: [what to add and why]

### Приоритет правок
| Приоритет   | Проблема | Шаг |
|-------------|----------|-----|
| 🔴 Критично  | ...      | N   |
| 🟠 Важно     | ...      | N   |
| 🟡 Уточнение | ...      | N   |
| 📌 Пробел    | ...      | N   |
```

Priority rules include gaps:
- 📌 **Gap** — not wrong, but the material would be materially better with a scoped, currency- or correctness-relevant addition.

Priority rules:
- 🔴 **Critical** — factually wrong in a way that produces broken code, wrong protocol, non-existent API, or a dangerous misunderstanding.
- 🟠 **Important** — technically inaccurate but not immediately breaking (e.g. wrong hardware spec, omitted newer version of a model or library).
- 🟡 **Minor** — misleading wording, outdated side comment, imprecise number, or overstated claim.

## Step 5 — Fix

After presenting the report, ask: **"Исправить всё?"**

If the user confirms:
- Fix all 🔴 and 🟠 items directly in the relevant `task.html` files.
- For 🟡 items — apply if the fix is unambiguous; otherwise note them as optional.
- Do **not** rewrite text that is correct. Surgical edits only.
- If a code example uses a non-existent API field or wrong SDK class, either replace it with the confirmed correct form or replace the example with a verified description plus a link to the official source.
- Apply 📌 gaps the user has agreed to: add the missing material **with a short explanation of why it matters** (e.g. why keys come from the environment, what a skipped step does), not just a bare line of code. Match the surrounding density and keep deliberately minimal examples minimal.
- After all edits, briefly summarize what changed.

## Search agent guidelines

Each agent must:
- Prioritize: official docs > GitHub source files (`.proto`, `README.md`, source code) > official changelogs > official blog posts.
- Explicitly distrust: third-party tutorials, community articles, Q&A sites, cached AI-generated content.
- For any technology, also check the official deprecation page or migration guide for the current year.
- When in doubt about whether a feature or parameter exists, check the source code or proto definition directly — documentation sometimes lags behind.

## What NOT to verify

- Pedagogical choices (lesson structure, example selection, explanation depth).
- The **completeness/runnability** of code marked as illustrative or simplified (e.g. `# упрощённая схема`) — a minimal example may legitimately omit steps. But its **API surface is still in scope**: even illustrative code must use real imports, real class names, and correct signatures. Verify those; only skip judging it for being incomplete.
- Media or asset placeholders (images, audio files).
- General engineering principles with no version-specific anchor (e.g. "gRPC has lower overhead than HTTP/1.1").
