# PriorityWhitelistRecord

DDB row tracking one uploaded whitelist through its lifecycle. One row per `priority_whitelist_id`.

Lifecycle: `started` → `confirmed` → `validated` → (`replaced` | `invalid` | `expired` | `abandoned`).

## Fields

Status-invariant:

**priority_whitelist_id** — string (UUID v4), required
  PK. Shared with the apply event + S3 object.

**region** — string (AWS region), required
  Region of origin.

**s3_key** — string, required
  `whitelists/{YYYY}/{MM}/{DD}/{id}.csv`.

**status** — enum, required
  Lifecycle marker.

**valid_until** — string (ISO 8601 UTC), required
  TTL marker; non-terminal rows past this lazily transition to `expired`.

**created_at**, **updated_at** — string (ISO 8601 UTC), required
  Insertion / last-mutation.

Status-dependent:

**row_count** — integer ≥ 0
  • `started`, `confirmed`: null
  • `validated`, `replaced`, `expired`, `abandoned`: set during validation
  • `invalid`: usually null; set if failure mid-stream

**error** — string
  • `invalid`: required — first failure or guard rejection reason
  • else: null

## Validation

zod schema at [priority-whitelist.schema.ts:8](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/upload/priority-whitelist.schema.ts#L8) applied on every DDB hydrate and pre-`put`:

```ts
PriorityWhitelistRecordSchema = z.object({
  priority_whitelist_id: z.string().uuid(),
  region:                z.enum(SUPPORTED_REGIONS),
  s3_key:                z.string().regex(/^whitelists\/\d{4}\/\d{2}\/\d{2}\/[0-9a-f-]+\.csv$/),
  status:                z.enum(['started','confirmed','validated','replaced','invalid','expired','abandoned']),
  valid_until:           z.string().datetime(),
  row_count:             z.number().int().nonnegative().nullable(),
  error:                 z.string().nullable(),
  created_at:            z.string().datetime(),
  updated_at:            z.string().datetime(),
})
```

Status-transition rules enforced in the repository — concurrency guard at [upload.repository.ts:48](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/upload/upload.repository.ts#L48); per-transition writes below.

## Storage

**DynamoDB** (see [contract](../contracts/dynamodb.md)) — table `priority_whitelist`, partitioned by `priority_whitelist_id`. No TTL — `expired` is set, not deleted.

Defined: [priority-whitelist.entity.ts](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/upload/priority-whitelist.entity.ts) · migration [001-create-priority-whitelist.ts](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-migrations/src/migrations/001-create-priority-whitelist.ts).

### Written

[upload-link issuance](../flows/upload-link.md) · [upload.repository.ts:24](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/upload/upload.repository.ts#L24):

<pre>
on POST /api/v1/whitelist/upload-link:
  id ← uuid()
  put PriorityWhitelistRecord (<a href="../contracts/dynamodb.md">DDB</a>) {
    id, region: request.region,
    s3_key:      "whitelists/" + today + "/" + id + ".csv",
    status:      "started",
    valid_until: now + ttl,
    created_at:  now,
    updated_at:  now,
  } condition: id not exists
</pre>

[upload-confirm](../flows/upload-confirm.md) · [confirm.controller.ts:18](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/upload/confirm.controller.ts#L18):

<pre>
on POST /api/v1/whitelist/{id}/confirm:
  record.status     ← confirmed
  record.updated_at ← now
  update record (<a href="../contracts/dynamodb.md">DDB</a>)
</pre>

[upload-validate-emit](../flows/upload-validate-emit.md) · [validation.repository.ts:18](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/validation/validation.repository.ts#L18):

<pre>
on validation done for record:
  on success: status ← validated, row_count ← N
  on failure: status ← invalid,   error     ← &lt;reason&gt;
  updated_at ← now
  update record (<a href="../contracts/dynamodb.md">DDB</a>)
</pre>

[lifecycle-replaced](../flows/lifecycle-replaced.md) · [lifecycle.consumer.ts:31](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/lifecycle/lifecycle.consumer.ts#L31):

<pre>
on <a href="PriorityWhitelistLifecycleEvent.md">PriorityWhitelistLifecycleEvent</a> (<a href="../contracts/kafka.md">Kafka</a>)(status=replaced):
  record.status     ← replaced
  record.updated_at ← now
  update record (<a href="../contracts/dynamodb.md">DDB</a>)
</pre>

### Read

[upload-link concurrency guard](../flows/upload-link.md) · [upload.repository.ts:48](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/upload/upload.repository.ts#L48):

<pre>
before issuing a new upload URL:
  latest ← query newest PriorityWhitelistRecord (<a href="../contracts/dynamodb.md">DDB</a>)
  if latest.status ∈ {started, confirmed, validated} and not stale:
    409
  else proceed
</pre>

[get-whitelist-status](../flows/get-whitelist-status.md) · [status.controller.ts:14](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/status/status.controller.ts#L14):

<pre>
on GET /api/v1/whitelist/{id}:
  record ← load PriorityWhitelistRecord (<a href="../contracts/dynamodb.md">DDB</a>) by id (404 if missing)
  return record
</pre>

## Lineage

### From

Built at [upload-link issuance](../flows/upload-link.md) · [upload.controller.ts:33](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/upload/upload.controller.ts#L33) from request body + server-minted fields:

<pre>
put PriorityWhitelistRecord (<a href="../contracts/dynamodb.md">DDB</a>) {
  id:          uuid(),
  region:      request.region,
  s3_key:      "whitelists/" + today + "/" + id + ".csv",
  status:      "started",
  valid_until: now + ttl,
  created_at:  now,
  updated_at:  now,
}
</pre>

### To

[PriorityWhitelistApplyEvent](PriorityWhitelistApplyEvent.md) — on validation success:

<pre>
emit <a href="PriorityWhitelistApplyEvent.md">PriorityWhitelistApplyEvent</a> (<a href="../contracts/kafka.md">Kafka</a>) { ...PriorityWhitelistRecord (<a href="../contracts/dynamodb.md">DDB</a>), player_count: record.row_count }
</pre>

[PriorityWhitelistLifecycleEvent](PriorityWhitelistLifecycleEvent.md) — on every status transition:

<pre>
emit <a href="PriorityWhitelistLifecycleEvent.md">PriorityWhitelistLifecycleEvent</a> (<a href="../contracts/kafka.md">Kafka</a>) { ...PriorityWhitelistRecord (<a href="../contracts/dynamodb.md">DDB</a>), occurred_at: now }
</pre>

[AnonymousUploadLinkResponse](AnonymousUploadLinkResponse.md) — at upload-link construction:

<pre>
return <a href="AnonymousUploadLinkResponse.md">AnonymousUploadLinkResponse</a> (<a href="../contracts/rest.md">HTTP</a>) { ...PriorityWhitelistRecord (<a href="../contracts/dynamodb.md">DDB</a>), upload_url }
</pre>
