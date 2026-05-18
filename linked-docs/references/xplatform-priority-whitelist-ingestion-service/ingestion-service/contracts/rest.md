# REST

HTTP endpoints ingestion-service serves over VPC Private Link. JSON over HTTPS, mTLS at the edge; no app-level token. Errors follow the per-app envelope `{ code, message, requestId }`.

## /api/v1/whitelist/*

Surface for whitelist upload, confirm, and status read. mTLS-authenticated. Concurrency-guarded against overlapping uploads.

### **Serve** POST /api/v1/whitelist/upload-link

Issue a presigned S3 PUT URL and pre-allocate a tracking record.

Request — inline:
- `region` — string (AWS region, required)

Response — [AnonymousUploadLinkResponse](../objects/AnonymousUploadLinkResponse.md):
- `priority_whitelist_id` — string (UUID v4)
- `upload_url` — string (URL)
- `s3_key` — string
- `valid_until` — string (ISO 8601 UTC)

Errors: `409` if a non-terminal, non-stale whitelist already exists for the caller.

[upload-link issuance](../flows/upload-link.md) · [upload.controller.ts:33](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/upload/upload.controller.ts#L33):

<pre>
on POST /api/v1/whitelist/upload-link:
  latest ← query newest <a href="../objects/PriorityWhitelistRecord.md">PriorityWhitelistRecord</a> (<a href="dynamodb.md">DDB</a>)
  if latest in non-terminal and not stale: 409
  record ← persist new <a href="../objects/PriorityWhitelistRecord.md">PriorityWhitelistRecord</a> (<a href="dynamodb.md">DDB</a>)
  url    ← <a href="s3.md">S3</a>.presign(put, record.s3_key, ttl=15m)
  return <a href="../objects/AnonymousUploadLinkResponse.md">AnonymousUploadLinkResponse</a> (HTTP) { ...<a href="../objects/PriorityWhitelistRecord.md">PriorityWhitelistRecord</a> (<a href="dynamodb.md">DDB</a>), upload_url: url }
</pre>

### **Serve** POST /api/v1/whitelist/{id}/confirm

Mark an upload as ready for validation. Transitions `started` → `confirmed`.

Request: empty.

Response: `204`.

Errors: `404` if `id` unknown; `409` if status ≠ `started`.

[upload-confirm](../flows/upload-confirm.md) · [confirm.controller.ts:18](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/upload/confirm.controller.ts#L18):

<pre>
on POST /api/v1/whitelist/{id}/confirm:
  record ← load <a href="../objects/PriorityWhitelistRecord.md">PriorityWhitelistRecord</a> (<a href="dynamodb.md">DDB</a>) by id (404 if missing)
  if record.status ≠ started: 409
  record.status     ← confirmed
  record.updated_at ← now
  update record
  emit <a href="../objects/PriorityWhitelistLifecycleEvent.md">PriorityWhitelistLifecycleEvent</a> (<a href="kafka.md">Kafka</a>)(status=confirmed)
</pre>

### **Serve** GET /api/v1/whitelist/{id}

Read current state of a whitelist row.

Request: path param `id`.

Response: subset of [PriorityWhitelistRecord](../objects/PriorityWhitelistRecord.md):
- `status` — enum
- `row_count` — integer ≥ 0, nullable
- `error` — string, nullable
- `valid_until` — string (ISO 8601 UTC)

Errors: `404` if `id` unknown.

[get-whitelist-status](../flows/get-whitelist-status.md) · [status.controller.ts:14](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/status/status.controller.ts#L14):

<pre>
on GET /api/v1/whitelist/{id}:
  record ← load <a href="../objects/PriorityWhitelistRecord.md">PriorityWhitelistRecord</a> (<a href="dynamodb.md">DDB</a>) by id (404 if missing)
  return { status, row_count, error, valid_until }
</pre>
