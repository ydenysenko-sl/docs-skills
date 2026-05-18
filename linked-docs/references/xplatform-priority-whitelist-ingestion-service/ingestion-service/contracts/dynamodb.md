# DynamoDB

Tables ingestion-service owns on its account-local DDB. Schemas managed by `apps/ingestion-migrations`.

## priority_whitelist.*

Single namespace covering whitelist lifecycle state.

### **Own** priority_whitelist

Per-whitelist lifecycle row.

Payload — [PriorityWhitelistRecord](../objects/PriorityWhitelistRecord.md):
- `priority_whitelist_id` — string (UUID v4) — PK
- `region` — string (AWS region)
- `s3_key` — string
- `status` — enum (`started` | `confirmed` | `validated` | `replaced` | `invalid` | `expired` | `abandoned`)
- `valid_until`, `created_at`, `updated_at` — string (ISO 8601 UTC)
- `row_count` — int ≥ 0, nullable
- `error` — string, nullable

Partition key: `priority_whitelist_id`. No sort key. No TTL — `expired` is set, not deleted.

Migration: [001-create-priority-whitelist.ts](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-migrations/src/migrations/001-create-priority-whitelist.ts).

#### Writers

[upload-link issuance](../flows/upload-link.md) · [upload.repository.ts:24](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/upload/upload.repository.ts#L24) — `started`:

<pre>
on POST /api/v1/whitelist/upload-link:
  id ← uuid()
  put <a href="../objects/PriorityWhitelistRecord.md">PriorityWhitelistRecord</a> (DDB) {
    id, region, s3_key, status: "started",
    valid_until, created_at, updated_at,
  } condition: id not exists
</pre>

[upload-confirm](../flows/upload-confirm.md) · [confirm.controller.ts:18](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/upload/confirm.controller.ts#L18) — `confirmed`:

<pre>
on POST /api/v1/whitelist/{id}/confirm:
  record.status     ← confirmed
  record.updated_at ← now
  update record
</pre>

[upload-validate-emit](../flows/upload-validate-emit.md) · [validation.repository.ts:18](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/validation/validation.repository.ts#L18) — `validated` / `invalid` / `expired`:

<pre>
on validation done for record:
  on success:        status ← validated, row_count ← N
  on row failure:    status ← invalid,   error     ← &lt;reason&gt;
  on valid_until past: status ← expired
  updated_at ← now
  update record
</pre>

[lifecycle-replaced](../flows/lifecycle-replaced.md) · [lifecycle.consumer.ts:31](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/lifecycle/lifecycle.consumer.ts#L31) — `replaced`:

<pre>
on <a href="../objects/PriorityWhitelistLifecycleEvent.md">PriorityWhitelistLifecycleEvent</a> (<a href="kafka.md">Kafka</a>)(status=replaced):
  record.status     ← replaced
  record.updated_at ← now
  update record
</pre>

[lifecycle-abandoned](../flows/lifecycle-abandoned.md) · [cleanup.cron.ts:12](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/lifecycle/cleanup.cron.ts#L12) — `abandoned`:

<pre>
on cron tick:
  for record where status ∈ {started, confirmed} and updated_at &lt; now - threshold:
    record.status     ← abandoned
    record.updated_at ← now
    update record
</pre>

#### Readers

[upload-link concurrency guard](../flows/upload-link.md) · [upload.repository.ts:48](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/upload/upload.repository.ts#L48):

<pre>
before issuing a new upload URL:
  latest ← query newest <a href="../objects/PriorityWhitelistRecord.md">PriorityWhitelistRecord</a> (DDB)
  if latest.status ∈ {started, confirmed, validated} and not stale: 409
  else proceed
</pre>

[get-whitelist-status](../flows/get-whitelist-status.md) · [status.controller.ts:14](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/status/status.controller.ts#L14):

<pre>
on GET /api/v1/whitelist/{id}:
  record ← load <a href="../objects/PriorityWhitelistRecord.md">PriorityWhitelistRecord</a> (DDB) by id (404 if missing)
  return { status, row_count, error, valid_until }
</pre>

[upload-validate-emit hydrate](../flows/upload-validate-emit.md) · [validation.consumer.ts:22](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/validation/validation.consumer.ts#L22):

<pre>
on ObjectCreated for whitelists/{date}/{id}.csv:
  record ← load <a href="../objects/PriorityWhitelistRecord.md">PriorityWhitelistRecord</a> (DDB) by id
</pre>
