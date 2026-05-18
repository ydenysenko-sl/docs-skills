---
name: storage-is-also-contract
description: "DynamoDB, SQL, Redis, S3 are first-class contracts — same convention as Kafka/REST/gRPC; each gets its own contracts/<backend>.md"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 31c6bcd4-f4cc-4fd3-bb6f-56058a3ed563
---

Storage backends (DynamoDB, SQL DB, Redis, S3) are contracts in the same sense as wire protocols (Kafka, REST, gRPC). They expose a typed surface that other parts of the system (or other services) depend on.

**Why:** state is contract. A table's primary key, sort key, and partition pattern are as load-bearing as a Kafka topic's partition key. Treating storage as informal "internal" hides cross-service dependencies that exist via shared tables, Redis namespaces, or S3 prefixes.

**How to apply:**

- Each storage backend a service writes/reads gets its own `contracts/<backend>.md` (e.g., `contracts/dynamodb.md`, `contracts/redis.md`, `contracts/s3.md`, `contracts/postgres.md`).
- Mirrors the Kafka contract shape: group by prefix → per-table/key H3 with verb (**Own** / **Read** / **Write**), inline payload schema, writers + readers with doc + code links.
- Object docs whose storage is a contract surface reference the contract on the first line of their Storage section, just like stream objects reference `kafka.md`. E.g., `**DynamoDB** (see [contract](../contracts/dynamodb.md)) — table priority_whitelist ...`.
- In pseudocode, the storage tag from [[feedback_pseudocode_names_storage]] links to the contract: `<a>PriorityWhitelistRecord</a> (<a href="../contracts/dynamodb.md">DDB</a>)`.

Pairs with [[feedback_pseudocode_names_storage]] (the storage tag) and contract-grouping convention from the linked-docs skill.
