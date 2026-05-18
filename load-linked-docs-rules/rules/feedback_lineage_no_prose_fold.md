---
name: ""
metadata: 
  node_type: memory
  originSessionId: 31c6bcd4-f4cc-4fd3-bb6f-56058a3ed563
---

In doc Lineage / derivation sections (and anywhere a "this object came from / feeds into that one" mapping appears), use pseudocode with the rest/spread operator. Never a prose summary in parentheses.

**Why:** prose folds bury the actual transformation. Pseudocode with `...` is scannable: spreads what's carried, names what's added or renamed.

**How to apply:**

Bad — prose fold:
> AnonymousUploadLinkResponse — at construction (`id`, `s3_key`, `valid_until` copied; `upload_url` added)

Good — pseudocode:
```
return AnonymousUploadLinkResponse { ...record, upload_url }
```

Good — with rename:
```
emit PriorityWhitelistApplyEvent { ...record, player_count: record.row_count }
```

Good — with addition:
```
emit PriorityWhitelistLifecycleEvent { ...record, occurred_at: now }
```

`...record` reads as "fields from record"; the precise subset is implied by the destination object's Fields section. For one or two fields total, show them explicitly without `...`.

Applies to: object docs Lineage › From / To, flow doc emit/assemble blocks, contract doc payload-construction pseudocode.

Pairs with [[feedback_pseudocode_names_storage]] (storage tag still applies — `PriorityWhitelistApplyEvent (Kafka) { ... }`).
