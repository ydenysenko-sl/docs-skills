---
name: linked-docs
description: Use when writing or reviewing project documentation that catalogs objects, flows, and contracts across one or more repos. Produces a navigable, link-verified docs tree with consistent terseness, abstraction layering, and inline cross-linking via pseudocode. Applies to docs of the form objects/<Name>.md, flows/<flow>.md, contracts/<protocol>.md, and cross-app/flows/<flow>.md.
---

# Linked Docs

A rulebook for structuring multi-repo project documentation as a self-cross-linking tree of objects, flows, and contracts. Apply whenever the user asks for documentation work — initial scaffold, a new object / flow / contract page, doc review, or cross-app synthesis.

This skill is a **guide / reference**, not an executor. A separate workflow skill handles automation (init, sync, verify); this one tells you what shape to write.

## Tree shape

`<docs-root>` is supplied per invocation; it can live anywhere (inside a repo, sibling to repos, or in a dedicated docs repo). Services are always nested under their owning repo; repo-level docs are optional siblings to the service folders.

```
<docs-root>/
  README.md                                ← cross-app catalog
  cross-app/
    flows/<flow-name>.md                   ← cross-app / cross-repo flows
  <repo>/                                  ← per-repo root (matches the git repo name)
    objects/<ObjectName>.md                ← optional: shared across services in this repo
    flows/<flow-name>.md                   ← optional: repo-level shared flows
    contracts/<protocol>.md                ← optional: shared contracts (e.g., common Kafka schemas)
    <service>/                             ← per-service (one folder per deployable / app)
      objects/<ObjectName>.md
      flows/<flow-name>.md
      contracts/                           ← one file per protocol / backend
        kafka.md
        rest.md
        grpc.md
        dynamodb.md
        sql.md
        redis.md
        s3.md
    <other-service>/
      ...
  <other-repo>/
    <service>/
      ...
```

Conventions:
- **Root level** = cross-app / synthesis layer.
- **`<repo>/<service>/`** = always. Even single-service repos nest one folder deep, so the layout is uniform.
- **`<repo>/<shared-section>/`** = optional. Use when objects, flows, or contracts genuinely span multiple services in the same repo (shared Kafka schema package, repo-wide config). Otherwise put everything under `<repo>/<service>/`.
- **Naming**: `<repo>` matches the git repo name (e.g., `xplatform-priority-whitelist-ingestion-service`); `<service>` matches the deployable / `apps/<service>` name (e.g., `ingestion-service`).

Path depths from a per-service object page (`<docs-root>/<repo>/<service>/objects/X.md`):

- Sibling object in same service: `Y.md`
- Same-service flow: `../flows/<flow>.md`
- Same-service contract: `../contracts/<protocol>.md`
- Same-repo shared object: `../../objects/<Name>.md`
- Other service in same repo: `../../<other-service>/objects/<Name>.md`
- Other repo + service: `../../../<other-repo>/<other-service>/objects/<Name>.md`
- Cross-app flow: `../../../cross-app/flows/<flow>.md`

From a cross-app flow (`<docs-root>/cross-app/flows/<flow>.md`):

- Per-service file: `../../<repo>/<service>/<section>/<Name>.md`
- Repo-level file: `../../<repo>/<section>/<Name>.md`

## Page templates

Read the canonical reference in [references/](references/) before authoring each kind. The templates below sketch structure; the references show the rules applied.

### Object page (`<repo>/objects/<ObjectName>.md`)

Section order:

1. **Title** (H1) — canonical object name
2. **Summary** — 1-3 sentences: role, producer, consumer, lifecycle / single-shot
3. **## Fields** — definition list; split under `Status-invariant:` / `Status-dependent:` when status drives field semantics
4. **## Validation** (if applicable) — zod schema inline + hand-written checks
5. **## Stream | Storage | Refs** — medium-specific section
6. **## Lineage** — at end; `### From` and `### To`

Field syntax (definition list, not table):

```
**name** — type (modifier, required/optional)
  One-line role / use.
```

Medium section conventions:
- Title reflects medium: `## Stream` for Kafka, `## Storage` for DDB / Redis / SQL / S3, `## Refs` for DTOs / synthetics
- First line: `**<Backend>** (see [contract](../contracts/<backend>.md)) — <key facts: topic / table / key / retention / partition>`
- Inline the wire / storage schema if small (Avro JSON, zod schema)
- Per-use subsection with verb H3:
  - Stream: `### Produced` / `### Consumed`
  - Storage: `### Written` / `### Read`
  - Refs: `### Constructed` / `### Returned to`
- Each entry: `[<flow>](../flows/<flow>.md) · [<file>:<line>](<path>)` then a `<pre>` pseudocode block

Lineage:
- `### From`: how this object is constructed — show field-level pseudocode
- `### To`: which objects derive significant fields. Use spread pseudocode — never prose folds

References:
- Kafka stream event: [references/xplatform-priority-whitelist-ingestion-service/ingestion-service/objects/PriorityWhitelistApplyEvent.md](references/xplatform-priority-whitelist-ingestion-service/ingestion-service/objects/PriorityWhitelistApplyEvent.md)
- DDB row with status-split fields + zod validation: [references/xplatform-priority-whitelist-ingestion-service/ingestion-service/objects/PriorityWhitelistRecord.md](references/xplatform-priority-whitelist-ingestion-service/ingestion-service/objects/PriorityWhitelistRecord.md)
- Anonymous HTTP response (synthetic): [references/xplatform-priority-whitelist-ingestion-service/ingestion-service/objects/AnonymousUploadLinkResponse.md](references/xplatform-priority-whitelist-ingestion-service/ingestion-service/objects/AnonymousUploadLinkResponse.md)

### Per-repo flow page (`<repo>/flows/<flow-name>.md`)

Section order:

1. **Title** (H1) — flow name (kebab-case)
2. **Summary** — 1-2 sentences
3. **## Trigger** — what initiates the flow (HTTP route, Kafka topic, cron, S3 event)
4. **## Flow** — `<pre>` + `<a>` pseudocode (see Pseudocode rules)
5. **## Sequence** — mermaid `sequenceDiagram`
6. **## Touches** — bullet list grouped by Kind (Storage / Stream / Contract); each line links the object / contract
7. **## Code** — bullet list mapping step → file:line

Reference: [references/xplatform-priority-whitelist-ingestion-service/ingestion-service/flows/upload-validate-emit.md](references/xplatform-priority-whitelist-ingestion-service/ingestion-service/flows/upload-validate-emit.md).

### Contract page (`<repo>/contracts/<protocol>.md`)

One file per protocol / backend. Storage backends (DDB, SQL, Redis, S3) **are** contracts — same shape as Kafka / REST.

Structure:

1. **H1** — protocol (`Kafka`, `REST`, `DynamoDB`, `S3`, `gRPC`, ...)
2. **Intro** — 1-2 sentences
3. **H2 prefix groups** — `notifying.cash_blast.priority_whitelist.*` / `/api/v1/whitelist/*` / `priority_whitelist.*` / `playson-priority-whitelist-{env}`
4. **H3 per topic / endpoint / table / key** — `### **<Verb>** <full-identifier>`:
   - Kafka: `**Produce**` / `**Consume**`
   - REST / gRPC: `**Serve**` (inbound) / `**Call**` (outbound)
   - Storage: `**Own**` (this repo's migrations define the schema)
5. **Per H3**:
   - Summary line
   - Payload — link the object + inline field bullets
   - Spec lines (retention / TTL / partition / lifecycle / migration)
   - Writers / Readers (or Emitters / Consumers) — each entry has doc link + code link + `<pre>` pseudocode
   - For multi-emitter / multi-writer topics: bullet list with per-entry pseudocode below the list

A topic that's produced and self-consumed appears under TWO H3s — once under `**Produce**`, once under `**Consume**`.

References:
- Kafka: [references/xplatform-priority-whitelist-ingestion-service/ingestion-service/contracts/kafka.md](references/xplatform-priority-whitelist-ingestion-service/ingestion-service/contracts/kafka.md)
- REST: [references/xplatform-priority-whitelist-ingestion-service/ingestion-service/contracts/rest.md](references/xplatform-priority-whitelist-ingestion-service/ingestion-service/contracts/rest.md)
- DynamoDB: [references/xplatform-priority-whitelist-ingestion-service/ingestion-service/contracts/dynamodb.md](references/xplatform-priority-whitelist-ingestion-service/ingestion-service/contracts/dynamodb.md)
- S3: [references/xplatform-priority-whitelist-ingestion-service/ingestion-service/contracts/s3.md](references/xplatform-priority-whitelist-ingestion-service/ingestion-service/contracts/s3.md)

### Cross-app flow page (`cross-app/flows/<flow-name>.md`)

Section order:

1. **Title** (H1)
2. **Summary** — 1-3 sentences end-to-end story
3. **## Flow** — `<pre>` numbered steps. Every step is a *cross-service* interaction (REST call, Kafka emit, S3 PUT, gRPC call) — no internal mutations
4. **## Sequence** — mermaid `sequenceDiagram` with all participants
5. **## Touches** — H3 per service, each listing Flows / Objects / Contracts as bulleted links. Final H3 `External` for non-repo actors

Reference: [references/cross-app/flows/priority-whitelist-e2e.md](references/cross-app/flows/priority-whitelist-e2e.md).

## Style rules

### Terseness

All documentation must be terse. Drop softening words ("note that", "it's worth mentioning"). No closing summaries. One line over two; one phrase over a sentence. Prefer pseudocode and bullet lists over prose. Ship the shorter version.

### No tables

Definition lists, bullet lists, and headed subsections only. Tables are hard to scan in markdown.

### Linking

- Bare relative markdown paths: `[name](../objects/X.md)`.
- Sibling links inside the same folder use bare filenames: `[X](X.md)`.
- Every emit / consume / write / read entry carries BOTH a doc link AND a code link.
- Use full topic names / endpoint paths / table names / S3 key patterns — no abbreviations like `apply.v1`.
- Self-references (object in its own page, storage in its own contract): bare. Cross-references: linked.

### Pseudocode

Use HTML `<pre>` blocks with inline `<a>` tags whenever canonical object names or storage tags need to be clickable. Standard markdown ``` fences do NOT render links inside.

Reserve fenced ``` blocks for literal code (Avro JSON, zod schema, raw config).

```
record ← load <a href="../objects/PriorityWhitelistRecord.md">PriorityWhitelistRecord</a> (<a href="../contracts/dynamodb.md">DDB</a>) by id
```

Storage tag rules:
- Every canonical object name in pseudocode is followed by `(<Storage>)`: `PriorityWhitelistRecord (DDB)` / `PriorityWhitelistApplyEvent (Kafka)` / `PriorityWhitelistCsv (S3)` / `AnonymousUploadLinkResponse (HTTP)`.
- The storage tag links to its contract page (cross-page). Self-page tag (e.g., `(Kafka)` inside `kafka.md`): bare.
- Aliases / local variables (`record.field`, `event.s3_key`) do NOT carry storage tags — the type was established when the canonical name first appeared.

Spread rules:
- Spread expressions use the canonical object name, not the alias: `{ ...PriorityWhitelistRecord (DDB), upload_url }`, NOT `{ ...record, upload_url }`. Both halves of the storage tag still apply.
- Lineage mappings always use spread pseudocode — never prose folds like "(id, s3_key copied; upload_url added)".

### Cross-app pseudocode (extra rules)

In `cross-app/flows/<flow>.md` only:

- Each step header is `<service> · <linked-flow>:` introducing the action. The flow link points to the per-repo flow that owns that step.

  ```
  4. ingestion-service · <a href="../../flows/upload-validate-emit.md">upload-validate-emit</a>:
     validate CSV at s3_key
     on success: emit ...
  ```

- External actors with no in-repo flow stay unlinked (`Spinlab → S3:`, `ClickHouse:` ...).

- Storage tag includes the owning service: `(<linked-service> <linked-storage>)`. Service link → that service's docs root (`../../` for the current repo, `../../<other-repo>/` for siblings). Storage link → that service's contract page.

  ```
  emit <a href="../../objects/X.md">X</a> (<a href="../../">ingestion-service</a> <a href="../../contracts/kafka.md">Kafka</a>)
  ```

- Abstraction stays at contract boundaries. No internal mutations like `record.status ← x` — those belong in per-repo flow pseudocode.

### Naming

- Objects: canonical type name from code (PascalCase).
- Inline / synthetic shapes with no formal type: `Anonymous<ConstructionSite>` (`AnonymousUploadLinkResponse` = response body of `POST /api/v1/whitelist/upload-link`).
- Flows: kebab-case verb-noun (`upload-validate-emit`, `draw-time-application`).
- Contracts: lowercased protocol / backend name (`kafka.md`, `rest.md`, `dynamodb.md`).

### Validation section

Include `## Validation` on an object page when runtime validation exists beyond what the transport schema (Avro / proto / DDB type) already enforces. Inline the zod schema if used; bullet-list hand-written checks. Place between Fields and the medium section.

### Status-dependent fields

If an object has fields whose presence or value semantics depend on a status enum, split the Fields list:

```
Status-invariant:

**id** — string, required
  ...

Status-dependent:

**error** — string
  • status=invalid: required — first failure reason
  • else: null
```

### Self-link convention

- Object's own name in its own page: bare (no self-link).
- Storage tag in its own contract doc: bare.
- Everywhere else: linked.

## Verification before "done"

Before considering any docs change complete:

1. Every emit / consume / write / read line has BOTH a doc link AND a code link.
2. Every canonical object name in pseudocode has a `(<Storage>)` tag.
3. Every storage tag in pseudocode is linked to a contract page — unless the current page IS the contract or owns the object.
4. Every relative link target exists.
5. No `...alias` in spreads — must be `...CanonicalName (Storage)`.
6. No prose-folded lineage mappings.
7. Cross-app pseudocode step headers use `<service> · <linked-flow>:` form.
8. Cross-app storage tags use `(<linked-service> <linked-storage>)` form.
9. Full topic / endpoint / table / key names used everywhere — no shortcuts.
10. Tables: none.

## References

Canonical examples — read before authoring:

- Objects (under `references/xplatform-priority-whitelist-ingestion-service/ingestion-service/objects/`):
  - [Kafka stream event — PriorityWhitelistApplyEvent](references/xplatform-priority-whitelist-ingestion-service/ingestion-service/objects/PriorityWhitelistApplyEvent.md)
  - [DDB row with lifecycle states + zod — PriorityWhitelistRecord](references/xplatform-priority-whitelist-ingestion-service/ingestion-service/objects/PriorityWhitelistRecord.md)
  - [Anonymous HTTP response — AnonymousUploadLinkResponse](references/xplatform-priority-whitelist-ingestion-service/ingestion-service/objects/AnonymousUploadLinkResponse.md)
- Per-repo flow: [upload-validate-emit](references/xplatform-priority-whitelist-ingestion-service/ingestion-service/flows/upload-validate-emit.md)
- Contracts (under `references/xplatform-priority-whitelist-ingestion-service/ingestion-service/contracts/`):
  - [Kafka](references/xplatform-priority-whitelist-ingestion-service/ingestion-service/contracts/kafka.md)
  - [REST](references/xplatform-priority-whitelist-ingestion-service/ingestion-service/contracts/rest.md)
  - [DynamoDB](references/xplatform-priority-whitelist-ingestion-service/ingestion-service/contracts/dynamodb.md)
  - [S3](references/xplatform-priority-whitelist-ingestion-service/ingestion-service/contracts/s3.md)
- Cross-app flow: [priority-whitelist-e2e](references/cross-app/flows/priority-whitelist-e2e.md)
