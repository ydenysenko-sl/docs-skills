---
name: cross-app-pseudocode-links-flows
description: Cross-app flow pseudocode must inline-link to the per-repo flow that owns each step
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ecd62b78-6124-4d51-b64b-011cef1cfad0
---

In cross-app flow documents, every pseudocode step performed by a service must inline-link the responsible per-repo flow doc.

**Why:** cross-app docs are navigation hubs. The reader scans the high-level steps and clicks into a per-repo flow for detail. Without inline flow links, the reader has to jump to a separate "Touches" section and figure out which flow corresponds to which step.

**How to apply:**

Bad — service name only:
```
4. ingestion-service: validate CSV at s3_key
```

Good — service · linked flow:
```
4. ingestion-service · <a href="../../flows/upload-validate-emit.md">upload-validate-emit</a>:
   validate CSV at s3_key
```

Pattern: every cross-service step is introduced as `<service> · <linked-per-repo-flow>:` followed by the high-level action. For client → service interactions, the receiver gets the flow link (`Spinlab → ingestion-service · <a>upload-link issuance</a>: POST ...`).

External actors with no in-repo flow (e.g., Spinlab, ClickHouse sink, pure S3 PUT) get no flow link — the step is bare.

Storage tag rule ([[feedback_pseudocode_names_storage]]) and canonical-object-link rule still apply on the same step.

Applies only to cross-app / cross-repo flow documents. Per-repo flow pseudocode is already inside its own flow; no inline self-link needed.
