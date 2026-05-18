---
name: spread-uses-canonical-object
description: "Pseudocode spread expressions use the canonical (linked) object name, not the local alias — `{ ...PriorityWhitelistRecord, ... }` not `{ ...record, ... }`"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 31c6bcd4-f4cc-4fd3-bb6f-56058a3ed563
---

In doc pseudocode that uses the spread/rest operator to carry fields from another object, the spread source must be the canonical object name (with a link), not the local alias.

**Why:** the spread expresses object-to-object derivation. Naming the type (with link) makes the source page one click away. Aliases like `record` lose that connection.

**How to apply:**

Bad — alias-based spread:
```
emit PriorityWhitelistApplyEvent (Kafka) { ...record, player_count: record.row_count }
```

Good — canonical-name spread with link:
```
emit PriorityWhitelistApplyEvent (Kafka) { ...<a href="...">PriorityWhitelistRecord</a> (<a href="...">DDB</a>), player_count: record.row_count }
```

The storage tag rule ([[feedback_pseudocode_names_storage]]) still applies — the canonical name in the spread carries `(Storage)` like every other canonical reference.

Local-variable field access (`record.row_count`, `record.s3_key`) stays as alias-based — only the type-level spread switches to the canonical name.

Applies to: object docs Lineage › From / To, contract doc payload-construction pseudocode, flow doc emit/assemble pseudocode, anywhere a `{ ...x, ... }` pattern appears in documentation.

Pairs with [[feedback_lineage_no_prose_fold]] (which mandated spread instead of prose) and [[feedback_pseudocode_names_storage]] (which mandates the storage tag).
