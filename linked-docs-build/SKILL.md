---
name: linked-docs-build
description: Use when generating linked-docs documentation from scratch for a multi-repo workspace. Runs a 9-phase pipeline of read→plan→write→verify agent cycles across parallel per-repo Agents and a cross-app synthesis pass. Only filename stability is persisted, via <docs-root>/names.json. Code is the only source of truth — tests, docs, and build output are excluded. Invoked via /linked-docs-build [filter].
---

# Linked Docs Build

End-to-end one-shot regenerator for a linked-docs tree. Every run wipes and rewrites all pages from source code. Only `<docs-root>/names.json` carries forward between runs — it pins canonical/anonymous object names and filenames so cross-page links stay stable.

The companion skill `linked-docs` is the *rulebook* — page shapes, pseudocode form, terseness, the 10-point verification checklist. This skill is the *executor*. Every dispatched Agent reads `~/.claude/skills/linked-docs/SKILL.md` itself; nothing here duplicates the rulebook.

## Trigger

```
/linked-docs-build [natural-language filter]
```

- Filter is free-form text naming a subset of repos: `"ingestion-service, kafka-contract"`, `"work on X and Y"`, `"only ingestion-service"`. Empty → all discovered repos.
- `<docs-root>` default = `<cwd>/docs/`. Override by saying `docs-root=<path>` in the prompt.

## Outputs

- `<docs-root>/README.md` — cross-app catalog
- `<docs-root>/cross-app/flows/*.md` — cross-repo flows
- `<docs-root>/<repo>/{objects,flows,contracts}/*.md` — per-repo pages
- `<docs-root>/names.json` — single persistent artifact (filename + display name per construction site)

## Exclusions (apply at every walk)

Tests: `**/*.{spec,test,e2e}.*`, `**/test/**`, `**/tests/**`, `**/__tests__/**`, `**/spec/**`, `**/e2e/**`
Build: `**/dist/**`, `**/build/**`, `**/.next/**`, `**/coverage/**`
Vendor: `**/node_modules/**`, `**/local-packages/**`
VCS / IDE: `**/.git/**`, `**/.idea/**`, `**/.vscode/**`
Docs / configs the writers must NOT read: `**/*.md`, `**/*.pdf`, `**/*.txt`, `**/CHANGELOG*`, `**/README*`

Code is the only source of truth. Existing docs are misleading by default.

## Pipeline

Nine phases. Orchestrator (main thread) drives phases 1, 5, 6, 9 and dispatches Agents for the rest. All Agents run `model: opus` and have `ultrathink` in their prompt. Every Agent runs `read → plan → write → verify` internally; that discipline appears in every template below.

### Phase 1 — Scope (orchestrator)

WHAT: parse filter, enumerate target repos, seed/load `names.json`, lay down the cross-cutting TODO list.
WHY: the rest of the pipeline fans out per repo; the scope must be settled and tracked before any dispatch.

Orchestrator actions:
- Parse the user prompt for repo names (match against directory entries under `<cwd>`).
- Discover candidate repos: each immediate subdir of `<cwd>` that contains `.git/` (or is itself a git repo). If none, treat `<cwd>` itself as the single repo.
- Narrow by filter. If filter names a repo that doesn't exist, halt with an error.
- Read `<docs-root>/names.json` if present; otherwise create `{}`.
- `TodoWrite` one entry per repo for discovery plus cross-app entries (plan · write · verify · link-sweep). Per-(repo, service) write+verify entries are appended after phase 2 returns the service list.
- Wipe `<docs-root>` of all `*.md` files under `<repo>/**/{objects,flows,contracts}/` and `cross-app/` subtrees. Leave `names.json` untouched. (Wipe happens here so phase-3 writes into clean dirs.)

### Phase 2 — Source Discovery (parallel Agents, one per repo)

WHAT: each Agent produces a categorized inventory of production source for its repo, with services enumerated as the unit of downstream fan-out.
WHY: downstream writers need a clean, grouped starting set, not raw `find` output. Categories surface architectural seams that map to linked-docs page kinds; per-service grouping drives phase-3 fan-out.

Dispatch (in a single message, one Agent block per repo):
- `subagent_type: general-purpose`
- `model: opus`
- Prompt: see [Discover agent template](#discover-agent-template), substituting `{{REPO}}` and `{{REPO_PATH}}`.

Each Agent returns a structured inventory whose top-level units are services (`apps/<name>`) plus an optional `_common` unit covering repo-shared code (`libs/common/`, `shared/`) AND the entire repo when there is no per-service code (e.g. `proto-contracts`, `kafka-schemas`). `_common` always maps to repo-level docs (no service folder). Keep the inventories in orchestrator context — they feed phase-3 fan-out.

### Phase 3 — Per-(Repo, Unit) Doc Write (parallel Agents, fresh dispatch)

WHAT: each Agent generates one fan-out unit's docs.
- Per-service Agent (`{{UNIT}}` = real service id): writes `<docs-root>/<repo>/<service>/{objects,flows,contracts}/*.md`.
- `_common` Agent (`{{UNIT}}` = `_common`): writes repo-level pages at `<docs-root>/<repo>/{objects,flows,contracts}/*.md`. No literal `_common/` directory on disk.

It also persists its own slice of `names.json[<repo>][<unit>]`.

WHY: services within a repo are independent surfaces; writers run in parallel across both axes. Fresh dispatch (not phase-2 agent) — discovery and authoring are distinct disciplines.

Dispatch:
- Per repo: if `_common` is in the phase-2 inventory, dispatch its Agent first; await; then dispatch all per-service Agents for that repo in parallel. Across repos, `_common` waves run in parallel; per-service waves run in parallel.
- `model: opus`, `subagent_type: general-purpose`.
- Prompt: see [Write agent template](#write-agent-template), substituting `{{REPO}}`, `{{UNIT}}`, `{{REPO_PATH}}`, `{{UNIT_PATH}}`, `{{DOCS_ROOT}}`, `{{INVENTORY}}` (the unit's slice of the phase-2 inventory).

Concurrency: `names.json` is sharded `[<repo>][<unit>]`, so parallel writes within a repo's per-service wave are safe. Each Agent reads then writes only its `[<repo>][<unit>]` key. Per-service Agents may *read* (not write) the sibling `[<repo>][_common]` slice to resolve links into repo-level shared pages.

### Phase 4 — Per-(Repo, Unit) Verify (parallel Agents, fresh dispatch)

WHAT: independent audit of each fan-out unit's freshly-written docs.
WHY: writers can't reliably verify their own output. Fresh eyes catch confirmation bias, hallucinated `file:line` refs, and rule violations.

Dispatch (parallel, one per (repo, unit) that was written in phase 3, including `_common`):
- `model: opus`, `subagent_type: general-purpose`.
- Prompt: see [Verify agent template](#verify-agent-template) with `{{SCOPE}}` = `<repo>/<service>` for per-service units, `<repo>` for `_common`. The verify Agent must limit its audit to files actually owned by its unit (per-service Agents audit `<repo>/<service>/**`; `_common` Agents audit `<repo>/*.md` and `<repo>/{objects,flows,contracts}/**` only — not sibling service folders).

Verify Agents are allowed to fix mechanical issues in place. Substantive failures (hallucinated objects, wrong facts) escalate back as a structured FAIL — orchestrator decides whether to re-dispatch phase 3 or surface to the user.

### Phase 5 — Orchestrator Reads Per-Repo Docs

WHAT: orchestrator `Read`s every page under `<docs-root>/<repo>/**/*.md` for all repos (covers both per-service folders and repo-level `_common` pages).
WHY: cross-app synthesis needs a mental model of all per-repo flows and contracts. Pages are terse (per the linked-docs spec) so this is the only point where the orchestrator pays a doc-content read cost.

### Phase 6 — Cross-App Plan (orchestrator)

WHAT: identify cross-repo seams and enumerate cross-app flows.
WHY: cross-app docs are derived synthesis, not direct reads of code; the plan must come from the per-repo docs.

Seams to look for, from per-repo `contracts/`:
- Kafka topics with producers in one repo and consumers in another → cross-app flow.
- gRPC services served by one repo and called by another → cross-app flow.
- REST endpoints served by one repo and called by another → cross-app flow.
- S3 buckets/keys with one writer and one or more readers.

`TodoWrite` one entry per cross-app flow page + one for `README.md`.

### Phase 7 — Cross-App Write (Agent, fresh dispatch)

WHAT: a single Agent writes `<docs-root>/cross-app/flows/*.md` and `<docs-root>/README.md`.
WHY: one author keeps terminology, naming, and abstraction level consistent across cross-app flows.

Dispatch one Agent: `model: opus`, prompt from [Cross-app write agent template](#cross-app-write-agent-template) with the planned flow list from phase 6.

### Phase 8 — Cross-App Verify (Agent, fresh dispatch)

WHAT: independent audit of the cross-app subtree.
WHY: same reason as phase 4. The cross-app rules (step header form, service-prefixed storage tag) are easy to violate; an audit pass catches them.

Dispatch one Agent: prompt from [Verify agent template](#verify-agent-template) with `{{SCOPE}}` = `cross-app`.

### Phase 9 — Workspace-Wide Link Sweep (orchestrator, scripted)

WHAT: run `check-links.py` over the entire `<docs-root>` and fix any remaining mismatches.
WHY: cross-app pages may link to per-repo pages with slightly different filenames than what was minted in phase 3 (e.g. casing, hyphenation). A final scripted pass catches every relative link that doesn't resolve.

Orchestrator actions:
- `Bash`: `python3 ~/.claude/skills/linked-docs-build/check-links.py <docs-root>`
- If broken links report — for each broken link:
  - If the target exists under a slightly-different name in the same directory → relink the source (NEVER rename per-repo pages — filename stability is a global invariant).
  - If the target does not exist anywhere → halt with a hard error citing the broken link. Do not silently create stubs.
- Rerun the script until it reports `OK`.
- Mark all TODO entries complete; print a one-paragraph summary of pages written.

---

## Agent prompt templates

The templates state goals and constraints. They do not script step-by-step procedure — Opus is the agent and can plan its own execution. Every template enforces the `read → plan → write → verify` discipline.

Substitute `{{...}}` placeholders before dispatching. Each prompt begins with the literal word `ultrathink` on its own line.

### Discover agent template

```
ultrathink

GOAL
Produce a structured inventory of production source files for repository `{{REPO}}` at `{{REPO_PATH}}`, grouped by architectural role.

WHY
Downstream agents will document the objects, flows, and contracts of this repo from your inventory. They need a categorized starting set: noise paths excluded, shared/common code distinguished from per-service code, files grouped so seams (controllers, kafka consumers, schemas, migrations, etc.) are obvious.

CONSTRAINTS
- Exclude: tests (`*.{spec,test,e2e}.*`, `test/`, `tests/`, `__tests__/`, `spec/`, `e2e/`), build output (`dist/`, `build/`, `.next/`, `coverage/`), vendor (`node_modules/`, `local-packages/`), VCS (`.git/`, `.idea/`, `.vscode/`), markdown/text docs (`*.md`, `*.txt`, `*.pdf`, `CHANGELOG*`, `README*`).
- Production source only. If a directory's purpose is ambiguous (e.g., `examples/`, `sandbox/`), inspect imports/usage and decide.
- Within the repo, distinguish: per-service / per-app code (e.g., `apps/<name>/src/...`) vs cross-service shared code (e.g., `libs/common/`, `shared/`). Both are production; the distinction matters to writers.
- Do not read source contents — file-path classification only. Use Glob and lightweight Grep at most.
- Do not cross repo boundaries.
- Do not read any markdown, PDF, or existing documentation files. Existing docs may be stale and must not seed your inventory.

DISCIPLINE (internal)
- READ: walk `{{REPO_PATH}}`, classify each file path.
- PLAN: TodoWrite an internal breakdown by category.
- WRITE: produce the inventory as your final structured response.
- VERIFY: confirm no excluded patterns leaked; confirm every category you claim is non-empty; confirm file paths are repo-relative.

OUTPUT
A structured inventory whose top-level units drive phase-3 fan-out. Units are: per-service (`apps/<name>` in a monorepo) and/or `_common` (repo-shared code OR the entire repo when no per-service code exists).

```
## {{REPO}} inventory

### Units

#### <service-id>           # one section per `apps/<name>` in monorepos; omit when the repo has no per-service code
- role: <one-line>
- source roots:
  - <relative path>
- entry-point surfaces:
  - HTTP controllers: <relative paths>
  - Kafka producers: <relative paths>
  - Kafka consumers: <relative paths>
  - gRPC servers / clients: <relative paths>
  - Cron / worker entry points: <relative paths>
  - S3 / DDB / SQL / Redis access points: <relative paths>
- schemas owned by this service: <relative paths>

#### _common                # emit when EITHER (a) the repo has shared code outside any service (e.g. `libs/common/`, `shared/`) OR (b) the repo has no per-service code at all (e.g. `proto-contracts`, `kafka-schemas`). Maps to repo-level docs at `<docs-root>/<repo>/{objects,flows,contracts}/`.
- source roots: <relative paths>
- entry-point surfaces (if any): <as above>
- schemas: <relative paths>
```

A monorepo emits N per-service units plus optional `_common`. A contract-only / single-service repo emits only `_common`. Omit empty subsections. Do not include excluded paths in any list.
```

### Write agent template

```
ultrathink

GOAL
Generate the linked-docs subtree for fan-out unit `{{UNIT}}` within repository `{{REPO}}`, grounded entirely in that unit's source code.
- If `{{UNIT}}` is a per-service id, write to `{{DOCS_ROOT}}/{{REPO}}/{{UNIT}}/{objects,flows,contracts}/*.md`.
- If `{{UNIT}}` is `_common`, write to `{{DOCS_ROOT}}/{{REPO}}/{objects,flows,contracts}/*.md` (no `_common/` folder).

WHY
This unit has no documentation yet, or whatever existed has been wiped. Downstream cross-app synthesis depends on these pages being terse, factually correct, and link-complete. Any hallucinated object, missing storage tag, or broken link breaks the rest of the run.

INPUTS
- Source code: `{{UNIT_PATH}}` (production only; the inventory below scopes what's worth reading). Per-service Agents read only within their service root; `_common` Agents read shared-code roots (or the whole repo when no per-service code exists).
- Inventory from phase 2 ({{REPO}}, unit {{UNIT}}):
{{INVENTORY}}
- Authoritative rulebook: `~/.claude/skills/linked-docs/SKILL.md` and `~/.claude/skills/linked-docs/references/` (read the references that match each page kind you author).
- Stable names: `{{DOCS_ROOT}}/names.json`, key `{{REPO}}.{{UNIT}}` (write) and `{{REPO}}._common` (read-only for per-service Agents, to resolve links into shared pages). Read existing entries for anonymous-object construction sites; reuse the existing filename and display name when the construction site matches. Mint new entries for new sites.
- Sibling shared docs (per-service Agents only, when `_common` exists): `{{DOCS_ROOT}}/{{REPO}}/{objects,flows,contracts}/*.md` — read to determine valid link targets for shared objects/contracts. Do not author there.

CONSTRAINTS
- The linked-docs rulebook is authoritative. Honor every rule, especially: no tables; pseudocode in `<pre>` with `<a>`; full topic/endpoint/table names (no abbreviations); storage tags on every canonical object in pseudocode; spread form for lineage (`{ ...CanonicalName (Storage), field }`); both a doc-link AND a code-link on every emit/consume/write/read entry.
- Ground every fact in code. Every `file:line` reference must point to a real symbol at that line within `{{UNIT_PATH}}`. Read the file at that line if in doubt.
- Do NOT read existing documentation, READMEs, or any `*.md` outside the linked-docs skill itself (and the sibling `_common` docs noted above). They may be stale and will mislead you.
- Update `{{DOCS_ROOT}}/names.json` only under the `{{REPO}}.{{UNIT}}` key. Do not touch other units' shards.
- If a fact you're about to document belongs to shared code (visible in `_common` docs or under the repo's shared-code roots), link to the existing `_common` page instead of duplicating it. If `_common` is missing a page you need, escalate as FAIL — do not author into `_common` yourself.
- Anonymous-object construction-site IDs follow this form (so they're reusable across runs):
  - `response:<METHOD> <path>` for HTTP response bodies, e.g. `response:POST /api/v1/whitelist/upload-link`
  - `request:<METHOD> <path>` for HTTP request bodies
  - `kafka-key:<topic>` / `kafka-value-inline:<topic>` for inline Kafka shapes not backed by a schema
  - `grpc-request:<service>.<rpc>` / `grpc-response:<service>.<rpc>`
  - `internal:<module>.<symbol>` for inline DTOs returned from internal funcs
- Be brutally terse. Drop softening words. Pseudocode over prose. The shorter version is the right version.

DISCIPLINE (internal)
- READ: source files indicated by the inventory; the linked-docs SKILL.md plus the reference(s) per page kind you are authoring; the `{{REPO}}` slice of `names.json`.
- PLAN: enumerate every canonical object (from code types), every anonymous I/O object (with its construction-site ID), every flow (with its trigger), every contract (per protocol/backend). Decide which names.json entries to reuse vs mint. TodoWrite your task list.
- WRITE: emit `<DOCS_ROOT>/{{REPO}}/{objects,flows,contracts}/*.md`. Persist your slice of `names.json`.
- VERIFY: run `python3 ~/.claude/skills/linked-docs-build/check-links.py {{DOCS_ROOT}}` and confirm OK for your subtree; eyeball the 10-point linked-docs checklist; re-Read ~3 file:line refs per page and confirm the symbol is present. Fix mechanical issues in place and retry once. Second failure → escalate.

OUTPUT
PASS with a one-line summary per page kind authored, OR FAIL with structured findings (rule violated, page, why uncorrectable).
```

### Verify agent template

```
ultrathink

GOAL
Independently verify `{{DOCS_ROOT}}/{{SCOPE}}/` for correctness, completeness, and link integrity against the linked-docs spec.

WHY
The author of these pages can't reliably catch their own confirmation bias, hallucinated `file:line` refs, or rule violations. Your job is fresh eyes. You audit; you fix only mechanical violations in place; you escalate substantive issues.

INPUTS
- Pages under audit: `{{DOCS_ROOT}}/{{SCOPE}}/**/*.md`
- Authoritative rulebook: `~/.claude/skills/linked-docs/SKILL.md` and `~/.claude/skills/linked-docs/references/`
- Source code (only for sampled `file:line` ref re-resolution; you do not re-discover objects)

CONSTRAINTS
- Fix in place: relative-link relinks, missing storage tag, `...alias` → `...CanonicalName (Storage)`, abbreviated topic/endpoint names → full names, missing service-prefix on cross-app storage tags, missing `<a>` on a canonical object in pseudocode, table → equivalent definition/bullet list.
- Do not rename files. Filename stability is a global invariant — relink the source side of a broken link instead.
- Do not edit source code.
- Do not silently rewrite a page because you'd have authored it differently. Substantive issues (hallucinated object, wrong fact in pseudocode, missing flow) → escalate, do not rewrite.
- Bound: 1 retry after fix. Second failure → return FAIL with structured findings.

DISCIPLINE (internal)
- READ: every page under `{{SCOPE}}`; the linked-docs SKILL.md and references; sampled source for ref re-resolution.
- PLAN: TodoWrite the check list: (1) `python3 ~/.claude/skills/linked-docs-build/check-links.py {{DOCS_ROOT}}` filtered to your scope; (2) 10-point linked-docs checklist per page; (3) sample ~3 `file:line` refs per page, re-Read and confirm the symbol is at that line.
- WRITE: apply mechanical fixes.
- VERIFY: re-run every check. PASS once all pass.

OUTPUT
PASS, or FAIL with a structured list of unfixable findings (rule violated, page, why uncorrectable).
```

### Cross-app write agent template

```
ultrathink

GOAL
Author `{{DOCS_ROOT}}/cross-app/flows/*.md` and `{{DOCS_ROOT}}/README.md`, synthesizing the cross-repo seams already documented per-repo.

WHY
Per-repo docs describe each repo's view of a seam. Cross-app docs tell the end-to-end story across repos, using a stricter pseudocode form (service-prefixed flow links in step headers; service-prefixed storage tags). A single author keeps terminology and abstraction consistent.

INPUTS
- Per-repo docs (already written and verified): `{{DOCS_ROOT}}/<repo>/**/*.md`
- Cross-app flows to author (from orchestrator plan):
{{PLANNED_FLOWS}}
- Authoritative rulebook: `~/.claude/skills/linked-docs/SKILL.md`; in particular, read `~/.claude/skills/linked-docs/references/cross-app/flows/view-owner-profile-with-visits.md` for cross-app pseudocode form.
- `{{DOCS_ROOT}}/names.json` (read-only — phase 3 already minted names; just look up existing entries when you need a display name).

CONSTRAINTS
- Do NOT read source code. All facts in cross-app docs derive from per-repo docs.
- Cross-app pseudocode rules (these are easy to violate):
  - Step header form: `<service> · <linked-flow>:` introducing the action. Service link points to that service's docs root; flow link points to the per-repo flow.
  - External actors (browsers, mobile clients, third-party APIs, ...) stay unlinked.
  - Storage tag form: `(<linked-service> <linked-storage>)` — both halves linked.
  - No internal mutations in cross-app pseudocode (no `record.status ← X`). Abstraction stays at contract boundaries.
- `README.md` is a cross-app catalog: one-line summary per cross-app flow with a link, one-line summary per repo with a link to that repo's docs root.
- Every link must be a relative path that will resolve.

DISCIPLINE (internal)
- READ: per-repo docs needed for each planned flow; the linked-docs SKILL.md plus the cross-app reference; `names.json`.
- PLAN: per cross-app flow, enumerate the service participants, the ordered cross-service interactions, and the touched objects/contracts per participant. TodoWrite a task list (one per page).
- WRITE: emit each `<DOCS_ROOT>/cross-app/flows/<flow>.md` and `<DOCS_ROOT>/README.md`.
- VERIFY: run `python3 ~/.claude/skills/linked-docs-build/check-links.py {{DOCS_ROOT}}` and confirm OK across your output; eyeball the cross-app-specific rules; fix mechanical issues; retry once.

OUTPUT
PASS with a brief summary, OR FAIL with structured findings.
```

---

## `names.json` shape

Single JSON file at `<docs-root>/names.json`. Sharded by repo so parallel phase-3 writers touch disjoint slices. Cross-app entries (if needed) live under the reserved `_cross_app` key.

```
{
  "<repo-name>": {
    "<unit>": {                              // per-service id, or "_common"
      "<construction-site-id>": {
        "name": "AnonymousUploadLinkResponse",
        "file": "AnonymousUploadLinkResponse.md"
      },
      ...
    },
    ...
  },
  "_cross_app": { ... },
  "_meta": {
    "version": 1,
    "last_run_iso": "2026-05-18T..."
  }
}
```

Construction-site IDs (canonical forms; used as JSON keys, exact-match between runs):
- `response:<METHOD> <path>` — HTTP response body
- `request:<METHOD> <path>` — HTTP request body
- `kafka-key:<topic>` / `kafka-value-inline:<topic>` — inline Kafka shapes (not Avro-backed)
- `grpc-request:<service>.<rpc>` / `grpc-response:<service>.<rpc>`
- `internal:<module>.<symbol>` — inline DTOs from internal funcs

Canonical objects (named types in code) also get an entry here, keyed by the canonical type name itself — `"PriorityWhitelistRecord": { name: "PriorityWhitelistRecord", file: "PriorityWhitelistRecord.md" }` — so the file pinning is uniform and any future rename in code can be handled by editing one place.

## Defaults summary

| Setting | Default | Override |
|--|--|--|
| Skill folder | `~/.claude/skills/linked-docs-build/` | — |
| Slash command | `/linked-docs-build` | — |
| `<docs-root>` | `<cwd>/docs/` | `docs-root=<path>` in prompt |
| Filter | all discovered repos | natural-language repo names in prompt |
| Agent model | `opus` | — |
| Agent discipline | `ultrathink` keyword + read→plan→write→verify | — |
| Verify retry budget | 1 retry | — |
| Link-check script | `~/.claude/skills/linked-docs-build/check-links.py` | — |
| linked-docs rulebook | `~/.claude/skills/linked-docs/` | — |
| Phase 3/4 fan-out unit | per (repo, service) plus `_common` (repo-level shared docs) | — |

(Tables are forbidden in the *generated* docs but fine here in the runbook.)
