# Kafka

Topics ingestion-service produces and consumes on the management cluster. Avro-typed, backward-compatible. Schemas live in [kafka-contract/schemas/](../../../../../kafka-contract/schemas/) and publish as per-topic NPM packages.

## notifying.cash_blast.priority_whitelist.*

Partition key on every topic: `priority_whitelist_id`. Every event carries a `region` field for multi-region observability.

### **Produce** notifying.cash_blast.priority_whitelist.apply.v1

Signals a validated whitelist is ready; processor must swap on the next draw.

Payload — [PriorityWhitelistApplyEvent](../objects/PriorityWhitelistApplyEvent.md):
- `priority_whitelist_id` — string (UUID v4)
- `region` — string (AWS region)
- `s3_key` — string
- `valid_until` — string (ISO 8601 UTC)
- `player_count` — int ≥ 0

Retention 7 days.

Emitted by [upload-validate-emit](../flows/upload-validate-emit.md) · [emit.service.ts:42](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/emit/emit.service.ts#L42):

<pre>
on validation success for record:
  emit <a href="../objects/PriorityWhitelistApplyEvent.md">PriorityWhitelistApplyEvent</a> (Kafka) {
    priority_whitelist_id: record.id,
    region:                record.region,
    s3_key:                record.s3_key,
    valid_until:           record.valid_until,
    player_count:          record.row_count,
  }
</pre>

External consumer — `cash-blast-processor-service` · [draw-time-application](../../../../../cash-blast-processor-service/cash-blast-processor/flows/draw-time-application.md) · [whitelist.consumer.ts:18](../../../../../cash-blast-processor-service/apps/processor/src/consumers/whitelist.consumer.ts#L18):

<pre>
on <a href="../objects/PriorityWhitelistApplyEvent.md">PriorityWhitelistApplyEvent</a> (Kafka):
  if event.region ≠ ours or event.valid_until past: skip
  csv ← read <a href="../objects/PriorityWhitelistCsv.md">PriorityWhitelistCsv</a> (<a href="s3.md">S3</a>) at event.s3_key
  swap active whitelist cache
  emit <a href="../objects/PriorityWhitelistLifecycleEvent.md">PriorityWhitelistLifecycleEvent</a> (Kafka)(status=replaced)
</pre>

### **Produce** notifying.cash_blast.priority_whitelist.lifecycle.v1

Status transitions for a whitelist row.

Payload — [PriorityWhitelistLifecycleEvent](../objects/PriorityWhitelistLifecycleEvent.md):
- `priority_whitelist_id` — string (UUID v4)
- `region` — string (AWS region)
- `status` — enum (`started` | `confirmed` | `validated` | `replaced` | `invalid` | `expired` | `abandoned`)
- `error` — string, optional (set on `invalid`)
- `occurred_at` — string (ISO 8601 UTC)

Retention 7 days.

Emitted by:

- [upload-link issuance](../flows/upload-link.md) · [upload.controller.ts:33](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/upload/upload.controller.ts#L33) — `started`
- [upload-confirm](../flows/upload-confirm.md) · [confirm.controller.ts:18](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/upload/confirm.controller.ts#L18) — `confirmed`
- [upload-validate-emit](../flows/upload-validate-emit.md) · [emit.service.ts:42](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/emit/emit.service.ts#L42) — `validated` / `invalid` / `expired`
- [lifecycle-abandoned](../flows/lifecycle-abandoned.md) · [cleanup.cron.ts:12](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/lifecycle/cleanup.cron.ts#L12) — `abandoned`

<pre>
on every status transition:
  emit <a href="../objects/PriorityWhitelistLifecycleEvent.md">PriorityWhitelistLifecycleEvent</a> (Kafka) { ...<a href="../objects/PriorityWhitelistRecord.md">PriorityWhitelistRecord</a> (<a href="dynamodb.md">DDB</a>), occurred_at: now }
</pre>

Sinks: ClickHouse Kafka engine → `xeye_prod.cash_blast_priority_whitelist_history` (no in-repo code); self-consumed (see below) on `replaced`.

> `replaced` is **not** emitted here — it originates in `cash-blast-processor-service` and is consumed here.

### **Consume** notifying.cash_blast.priority_whitelist.lifecycle.v1

Self-consumed on `replaced` to flip the ingestion-side ACTIVE pointer.

Payload — same as the Produce section above.

Consumed by [lifecycle-replaced](../flows/lifecycle-replaced.md) · [lifecycle.consumer.ts:31](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/lifecycle/lifecycle.consumer.ts#L31):

<pre>
on <a href="../objects/PriorityWhitelistLifecycleEvent.md">PriorityWhitelistLifecycleEvent</a> (Kafka):
  if status ≠ replaced: ignore
  record ← load <a href="../objects/PriorityWhitelistRecord.md">PriorityWhitelistRecord</a> (<a href="dynamodb.md">DDB</a>) by id
  record.status     ← replaced
  record.updated_at ← now
  update record
</pre>

### **Consume** notifying.cash_blast.priority_whitelist.config_changed.v1

Cache-invalidation signal for runtime config. Primary delivery; gRPC `GetConfig` is the cache-miss fallback.

Payload — [PriorityWhitelistConfigChangedEvent](../objects/PriorityWhitelistConfigChangedEvent.md):
- `region` — string (AWS region)
- `changed_at` — string (ISO 8601 UTC)

Consumed by [config-refresh](../flows/config-refresh.md) · [config.consumer.ts:24](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/config/config.consumer.ts#L24):

<pre>
on <a href="../objects/PriorityWhitelistConfigChangedEvent.md">PriorityWhitelistConfigChangedEvent</a> (Kafka):
  invalidate local config cache
  // next read lazily fetches via gRPC GetConfig
</pre>
