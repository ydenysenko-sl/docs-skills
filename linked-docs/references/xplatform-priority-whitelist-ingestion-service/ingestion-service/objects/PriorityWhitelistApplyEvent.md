# PriorityWhitelistApplyEvent

Emitted by ingestion-service on validation success. Consumed by cash-blast-processor per draw to swap the active whitelist. Single-shot, immutable.

## Fields

**priority_whitelist_id** — string (UUID v4), required
  Stable id. Partition key.

**region** — string (AWS region), required
  Multi-region observability tag.

**s3_key** — string, required
  `playson-priority-whitelist-{env}/whitelists/{YYYY}/{MM}/{DD}/{id}.csv`.

**valid_until** — string (ISO 8601 UTC), required
  TTL boundary; past this, processor bypasses.

**player_count** — integer ≥ 0, required
  Validated row count. Drives empty-whitelist alerting.

## Validation

Pre-emit checks at [emit.service.ts:42](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/emit/emit.service.ts#L42):

- `region` ∈ supported regions
- `valid_until` > now (else `lifecycle(expired)`)
- `player_count` ≥ 1 (else record `invalid`)

Avro enforces shape at producer. Consumers re-check region + `valid_until` only.

## Stream

**Kafka** (see [contract](../contracts/kafka.md)) — topic `notifying.cash_blast.priority_whitelist.apply.v1`, partitioned by `priority_whitelist_id`, retention 7 days, management cluster only.

Defined: [apply.v1.avsc](../../../../../kafka-contract/schemas/notifying.cash_blast.priority_whitelist.apply.v1/notifying.cash_blast.priority_whitelist.apply.v1.avsc) · pkg `@playson-toolkit/kafka-contract-notifying-cash-blast-priority-whitelist-apply`. Schema:

```avro
{
  "type": "record",
  "name": "PriorityWhitelistApplyEvent",
  "fields": [
    { "name": "priority_whitelist_id", "type": "string" },
    { "name": "region",                "type": "string" },
    { "name": "s3_key",                "type": "string" },
    { "name": "valid_until",           "type": "string" },
    { "name": "player_count",          "type": "int"    }
  ]
}
```

### Produced

[upload-validate-emit](../flows/upload-validate-emit.md) · [emit.service.ts:42](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/emit/emit.service.ts#L42):

<pre>
on validation success for record:
  emit PriorityWhitelistApplyEvent (<a href="../contracts/kafka.md">Kafka</a>) {
    priority_whitelist_id: record.id,
    region:                record.region,
    s3_key:                record.s3_key,
    valid_until:           record.valid_until,
    player_count:          record.row_count,
  }
</pre>

### Consumed

External — `cash-blast-processor-service` · [draw-time-application](../../../../../cash-blast-processor-service/cash-blast-processor/flows/draw-time-application.md) · [whitelist.consumer.ts:18](../../../../../cash-blast-processor-service/apps/processor/src/consumers/whitelist.consumer.ts#L18):

<pre>
on PriorityWhitelistApplyEvent (<a href="../contracts/kafka.md">Kafka</a>):
  if event.region ≠ ours or event.valid_until past: skip
  csv ← read <a href="PriorityWhitelistCsv.md">PriorityWhitelistCsv</a> (<a href="../contracts/s3.md">S3</a>) at event.s3_key
  swap active whitelist cache
  emit <a href="PriorityWhitelistLifecycleEvent.md">PriorityWhitelistLifecycleEvent</a> (<a href="../contracts/kafka.md">Kafka</a>)(status=replaced)
</pre>

## Lineage

### From

[PriorityWhitelistRecord](PriorityWhitelistRecord.md) — on validation success:

<pre>
emit PriorityWhitelistApplyEvent (<a href="../contracts/kafka.md">Kafka</a>) { ...<a href="PriorityWhitelistRecord.md">PriorityWhitelistRecord</a> (<a href="../contracts/dynamodb.md">DDB</a>), player_count: record.row_count }
</pre>

### To

None — consumed externally by `cash-blast-processor-service`.
