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
- **Naming**: `<repo>` matches the git repo name (e.g., `spring-petclinic-microservices`); `<service>` matches the deployable / `<service>` module name (e.g., `customers-service`).

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
- First line: `**<Backend>** (see `[contract]` linked to `../contracts/<backend>.md`) — <key facts: topic / table / key / retention / partition>`
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
- JPA entity (parent, Bean Validation): [references/spring-petclinic-microservices/customers-service/objects/Owner.md](references/spring-petclinic-microservices/customers-service/objects/Owner.md)
- JPA entity (child of Owner, FK relation): [references/spring-petclinic-microservices/customers-service/objects/Pet.md](references/spring-petclinic-microservices/customers-service/objects/Pet.md)
- Synthetic HTTP response composing parent + child: [references/spring-petclinic-microservices/customers-service/objects/OwnerSummaryResponse.md](references/spring-petclinic-microservices/customers-service/objects/OwnerSummaryResponse.md)

### Per-repo flow page (`<repo>/flows/<flow-name>.md`)

Section order:

1. **Title** (H1) — flow name (kebab-case)
2. **Summary** — 1-2 sentences
3. **## Trigger** — what initiates the flow (HTTP route, Kafka topic, cron, S3 event)
4. **## Flow** — `<pre>` + `<a>` pseudocode (see Pseudocode rules)
5. **## Sequence** — mermaid `sequenceDiagram`
6. **## Touches** — bullet list grouped by Kind (Storage / Stream / Contract); each line links the object / contract
7. **## Code** — bullet list mapping step → file:line

Reference: [references/spring-petclinic-microservices/customers-service/flows/upsert-owner-and-pets.md](references/spring-petclinic-microservices/customers-service/flows/upsert-owner-and-pets.md).

### Contract page (`<repo>/contracts/<protocol>.md`)

One file per protocol / backend. Storage backends (DDB, SQL, Redis, S3) **are** contracts — same shape as Kafka / REST.

Structure:

1. **H1** — protocol (`Kafka`, `REST`, `DynamoDB`, `S3`, `gRPC`, ...)
2. **Intro** — 1-2 sentences
3. **H2 prefix groups** — `petclinic.*` / `/owners/*` / `customers-service` / `springCloudBus`
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
- MySQL (relational store with parent/child tables): [references/spring-petclinic-microservices/customers-service/contracts/mysql.md](references/spring-petclinic-microservices/customers-service/contracts/mysql.md)
- REST (HTTP endpoints served): [references/spring-petclinic-microservices/customers-service/contracts/rest.md](references/spring-petclinic-microservices/customers-service/contracts/rest.md)
- Eureka (service discovery registration): [references/spring-petclinic-microservices/customers-service/contracts/eureka.md](references/spring-petclinic-microservices/customers-service/contracts/eureka.md)
- Spring Cloud Bus (async refresh events over RabbitMQ): [references/spring-petclinic-microservices/customers-service/contracts/bus.md](references/spring-petclinic-microservices/customers-service/contracts/bus.md)

### Cross-app flow page (`cross-app/flows/<flow-name>.md`)

Section order:

1. **Title** (H1)
2. **Summary** — 1-3 sentences end-to-end story
3. **## Flow** — `<pre>` numbered steps. Every step is a *cross-service* interaction (REST call, Kafka emit, S3 PUT, gRPC call) — no internal mutations
4. **## Sequence** — mermaid `sequenceDiagram` with all participants
5. **## Touches** — H3 per service, each listing Flows / Objects / Contracts as bulleted links. Final H3 `External` for non-repo actors

Reference: [references/cross-app/flows/view-owner-profile-with-visits.md](references/cross-app/flows/view-owner-profile-with-visits.md).

## Style rules

### Terseness

All documentation must be terse. Drop softening words ("note that", "it's worth mentioning"). No closing summaries. One line over two; one phrase over a sentence. Prefer pseudocode and bullet lists over prose. Ship the shorter version.

### No tables

Definition lists, bullet lists, and headed subsections only. Tables are hard to scan in markdown.

### Linking

- Bare relative markdown paths: `[name](../objects/X.md)`.
- Sibling links inside the same folder use bare filenames: `[X](X.md)`.
- Every emit / consume / write / read entry carries BOTH a doc link AND a code link.
- Use full topic names / endpoint paths / table names / S3 key patterns — no abbreviations like `/owners` for `POST /owners` or `bus` for `springCloudBus`.
- Self-references (object in its own page, storage in its own contract): bare. Cross-references: linked.

### Pseudocode

Use HTML `<pre>` blocks with inline `<a>` tags whenever canonical object names or storage tags need to be clickable. Standard markdown ``` fences do NOT render links inside.

Reserve fenced ``` blocks for literal code (Avro JSON, JPA annotations, raw config).

```
owner ← load <a href="references/spring-petclinic-microservices/customers-service/objects/Owner.md">Owner</a> (<a href="references/spring-petclinic-microservices/customers-service/contracts/mysql.md">MySQL</a>) by id
```

Storage tag rules:
- Every canonical object name in pseudocode is followed by `(<Storage>)`: `Owner (MySQL)` / `Pet (MySQL)` / `OwnerSummaryResponse (HTTP)` / `RefreshRemoteApplicationEvent (Bus)`.
- The storage tag links to its contract page (cross-page). Self-page tag (e.g., `(MySQL)` inside `mysql.md`): bare.
- Aliases / local variables (`owner.firstName`, `pet.ownerId`) do NOT carry storage tags — the type was established when the canonical name first appeared.

Spread rules:
- Spread expressions use the canonical object name, not the alias: `{ ...Owner (MySQL), pets }`, NOT `{ ...owner, pets }`. Both halves of the storage tag still apply.
- Lineage mappings always use spread pseudocode — never prose folds like "(id, firstName, lastName copied; pets added)".

### Cross-app pseudocode (extra rules)

In `cross-app/flows/<flow>.md` only:

- Each step header is `<service> · <linked-flow>:` introducing the action. The flow link points to the per-repo flow that owns that step.

  ```
  2. api-gateway → customers-service · <a href="references/spring-petclinic-microservices/customers-service/flows/upsert-owner-and-pets.md">upsert-owner-and-pets</a> (read path):
     GET http://customers-service/owners/{id}
     ← OwnerSummaryResponse
  ```

- External actors with no in-repo flow stay unlinked (`browser → api-gateway:`, `RabbitMQ:` ...).

- Storage tag includes the owning service: `(<linked-service> <linked-storage>)`. Service link → that service's docs root (`../../` for the current repo, `../../<other-repo>/` for siblings). Storage link → that service's contract page.

  ```
  return <a href="references/spring-petclinic-microservices/customers-service/objects/OwnerSummaryResponse.md">OwnerSummaryResponse</a> (<a href="references/spring-petclinic-microservices/customers-service/">customers-service</a> <a href="references/spring-petclinic-microservices/customers-service/contracts/rest.md">HTTP</a>)
  ```

- Abstraction stays at contract boundaries. No internal mutations like `owner.firstName ← x` — those belong in per-repo flow pseudocode.

### Naming

- Objects: canonical type name from code (PascalCase).
- Inline / synthetic shapes with no formal type: `<Subject>SummaryResponse` / `Anonymous<ConstructionSite>` (e.g., `OwnerSummaryResponse` = response body of `GET /owners/{id}`).
- Flows: kebab-case verb-noun (`upsert-owner-and-pets`, `view-owner-profile-with-visits`).
- Contracts: lowercased protocol / backend name (`mysql.md`, `rest.md`, `eureka.md`, `bus.md`).

### Validation section

Include `## Validation` on an object page when runtime validation exists beyond what the transport schema (Avro / proto / JPA column type) already enforces. Inline the schema (Bean Validation, zod, etc.) if used; bullet-list hand-written checks. Place between Fields and the medium section.

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

- Objects (under `references/spring-petclinic-microservices/customers-service/objects/`):
  - [JPA entity, parent — Owner](references/spring-petclinic-microservices/customers-service/objects/Owner.md)
  - [JPA entity, child of Owner — Pet](references/spring-petclinic-microservices/customers-service/objects/Pet.md)
  - [Synthetic HTTP response — OwnerSummaryResponse](references/spring-petclinic-microservices/customers-service/objects/OwnerSummaryResponse.md)
- Per-repo flow: [upsert-owner-and-pets](references/spring-petclinic-microservices/customers-service/flows/upsert-owner-and-pets.md)
- Contracts (under `references/spring-petclinic-microservices/customers-service/contracts/`):
  - [MySQL](references/spring-petclinic-microservices/customers-service/contracts/mysql.md)
  - [REST](references/spring-petclinic-microservices/customers-service/contracts/rest.md)
  - [Eureka](references/spring-petclinic-microservices/customers-service/contracts/eureka.md)
  - [Spring Cloud Bus](references/spring-petclinic-microservices/customers-service/contracts/bus.md)
- Cross-app flow: [view-owner-profile-with-visits](references/cross-app/flows/view-owner-profile-with-visits.md)
