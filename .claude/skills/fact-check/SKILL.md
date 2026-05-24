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

Read `lesson.json` and all text steps (`task.html`) for that lesson.

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

### Приоритет правок
| Приоритет   | Проблема | Шаг |
|-------------|----------|-----|
| 🔴 Критично  | ...      | N   |
| 🟠 Важно     | ...      | N   |
| 🟡 Уточнение | ...      | N   |
```

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
- After all edits, briefly summarize what changed.

## Search agent guidelines

Each agent must:
- Prioritize: official docs > GitHub source files (`.proto`, `README.md`, source code) > official changelogs > official blog posts.
- Explicitly distrust: third-party tutorials, community articles, Q&A sites, cached AI-generated content.
- For any technology, also check the official deprecation page or migration guide for the current year.
- When in doubt about whether a feature or parameter exists, check the source code or proto definition directly — documentation sometimes lags behind.

## What NOT to verify

- Pedagogical choices (lesson structure, example selection, explanation depth).
- Code marked as illustrative or simplified (e.g. with a comment like `# упрощённая схема`).
- Media or asset placeholders (images, audio files).
- General engineering principles with no version-specific anchor (e.g. "gRPC has lower overhead than HTTP/1.1").
