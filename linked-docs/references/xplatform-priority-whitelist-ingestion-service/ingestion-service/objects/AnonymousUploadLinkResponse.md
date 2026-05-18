# AnonymousUploadLinkResponse

Response body of `POST /api/v1/whitelist/upload-link`. Built inline; no named DTO. Sole consumer: Spinlab. Named after construction site.

## Fields

**priority_whitelist_id** — string (UUID v4), required
  Newly minted. Spinlab correlates the upload with later lifecycle events.

**upload_url** — string (URL), required
  S3 presigned PUT URL. ~15 min validity.

**s3_key** — string, required
  Pre-agreed key the presigned URL is bound to.

**valid_until** — string (ISO 8601 UTC), required
  Whitelist TTL boundary (not the presigned URL's expiry).

## Refs

**HTTP** (see [REST contract](../contracts/rest.md)) — JSON response over HTTPS via VPC Private Link. No formal schema. Shape:

```
{
  priority_whitelist_id: string,
  upload_url:            string,
  s3_key:                string,
  valid_until:           string,
}
```

### Constructed

[upload-link issuance](../flows/upload-link.md) · [upload.controller.ts:33](../../../../../xplatform-priority-whitelist-ingestion-service/apps/ingestion-service/src/upload/upload.controller.ts#L33):

<pre>
on POST /api/v1/whitelist/upload-link:
  record ← persist new <a href="PriorityWhitelistRecord.md">PriorityWhitelistRecord</a> (<a href="../contracts/dynamodb.md">DDB</a>)
  return AnonymousUploadLinkResponse (<a href="../contracts/rest.md">HTTP</a>) {
    priority_whitelist_id: record.id,
    upload_url:            S3.presign(put, record.s3_key, ttl=15m),
    s3_key:                record.s3_key,
    valid_until:           record.valid_until,
  }
</pre>

### Returned to

Spinlab (external) — no in-repo consumer.

## Lineage

### From

[PriorityWhitelistRecord](PriorityWhitelistRecord.md) — at construction:

<pre>
return AnonymousUploadLinkResponse (<a href="../contracts/rest.md">HTTP</a>) { ...<a href="PriorityWhitelistRecord.md">PriorityWhitelistRecord</a> (<a href="../contracts/dynamodb.md">DDB</a>), upload_url }
</pre>

### To

None — returned to Spinlab over HTTPS; not consumed in-repo.
