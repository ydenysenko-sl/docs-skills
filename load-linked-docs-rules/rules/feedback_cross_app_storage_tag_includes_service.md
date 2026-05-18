---
name: cross-app-storage-tag-includes-service
description: "In cross-app flow pseudocode, the storage tag is (<service-name> <storage>) with both linked — disambiguates which service owns the surface"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ecd62b78-6124-4d51-b64b-011cef1cfad0
---

In cross-app / cross-repo flow docs, the storage tag in pseudocode must name BOTH the owning service and the storage medium, with both linked.

**Why:** per-repo docs have implicit service context; cross-app docs don't. `(S3)` alone is ambiguous when multiple services own S3 buckets. `(ingestion-service S3)` names the surface uniquely.

**How to apply:**

Bad — bare storage:
```
PUT <a>PriorityWhitelistCsv</a> (<a>S3</a>)
```

Good — service + storage, both linked:
```
PUT <a>PriorityWhitelistCsv</a> (<a href="../../">ingestion-service</a> <a href="../../contracts/s3.md">S3</a>)
```

Service name links to that service's docs root (e.g., `../../` from `cross-app/flows/`); storage links to the contract page within that service. The "owning" service is the producer / table owner / bucket owner — whichever repo's `contracts/<backend>.md` is the canonical definition.

External actors (Spinlab, ClickHouse sinks) get no service link — they don't have in-workspace docs.

Applies only to cross-app / cross-repo docs. Per-repo docs keep the bare `(S3)` / `(DDB)` / `(Kafka)` form since service context is implicit.

Pairs with [[feedback_pseudocode_names_storage]] (the base storage-tag rule) and [[feedback_storage_is_also_contract.md]] (storage IS a contract).
