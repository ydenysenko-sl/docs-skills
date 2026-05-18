---
name: pseudocode-must-name-storage
description: "In documentation pseudocode, every canonical object name must be tagged with its storage/medium in parens"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 31c6bcd4-f4cc-4fd3-bb6f-56058a3ed563
---

When writing pseudocode in documentation, every reference to an object by its canonical name must be followed by its storage / transport medium in parens.

**Why:** makes pseudocode self-describing about where each piece of state lives, so a reader doesn't need to chase a link to find out.

**How to apply:**

Tag the canonical object name with its medium:
- `record ← load PriorityWhitelistRecord (DDB) by id`
- `emit PriorityWhitelistApplyEvent (Kafka) { ... }`
- `stream PriorityWhitelistCsv (S3) rows`
- `return AnonymousUploadLinkResponse (HTTP) { ... }`
- `cached ← read SessionToken (Redis)`

Mediums: `DDB` / `Kafka` / `Redis` / `S3` / `HTTP` / `gRPC` / `in-memory`.

Aliases / local variables (`record`, `apply`, `response`) get no tag — the type was established when the name first appeared.

In `<pre>` blocks with inline `<a>` links, the tag goes outside the link:
`<a href="...">PriorityWhitelistRecord</a> (DDB)`.

Applies to flow docs, object docs (Storage/Stream/Refs/Lineage pseudocode), contract docs (emit/consume pseudocode), and any other doc with pseudocode referencing project objects. This is a documentation rule, not a code-comment rule.

Pairs with [[feedback_all_docs_terse]] — the tag is short for a reason.
