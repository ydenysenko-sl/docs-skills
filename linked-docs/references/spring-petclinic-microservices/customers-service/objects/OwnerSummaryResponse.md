# OwnerSummaryResponse

Response body of `GET /owners/{id}`. Synthetic shape composing [Owner](Owner.md) with embedded `pets[]`; no formal Java DTO — serialized straight from the JPA entity with `@JsonManagedReference` on `pets`. Consumed by api-gateway to render the owner-details page.

## Fields

**id** — int, required
  Owner PK.

**firstName**, **lastName** — string, required
  From [Owner](Owner.md).

**address**, **city**, **telephone** — string, required
  From [Owner](Owner.md).

**pets** — array, required (may be empty)
  Each element:
  - `id` — int
  - `name` — string
  - `birthDate` — string (ISO 8601 date)
  - `type` — `{ id: int, name: string }`

## Refs

**HTTP** (see [REST contract](../contracts/rest.md)) — JSON response over HTTP via api-gateway. No formal schema. Shape:

```
{
  id:        int,
  firstName: string,
  lastName:  string,
  address:   string,
  city:      string,
  telephone: string,
  pets: [
    { id: int, name: string, birthDate: string, type: { id: int, name: string } }
  ]
}
```

### Constructed

[GET /owners/{id}](../contracts/rest.md) · [OwnerResource.java](https://github.com/spring-petclinic/spring-petclinic-microservices/blob/main/spring-petclinic-customers-service/src/main/java/org/springframework/samples/petclinic/customers/web/OwnerResource.java):

<pre>
on GET /owners/{id}:
  owner ← load <a href="Owner.md">Owner</a> (<a href="../contracts/mysql.md">MySQL</a>) by id (404 if missing)
  return OwnerSummaryResponse (<a href="../contracts/rest.md">HTTP</a>) {
    ...<a href="Owner.md">Owner</a> (<a href="../contracts/mysql.md">MySQL</a>),
    pets: owner.pets,
  }
</pre>

### Returned to

api-gateway (external) — composed with visits-service `Visit[]` into the owner-details page; see [cross-app/flows/view-owner-profile-with-visits](../../../cross-app/flows/view-owner-profile-with-visits.md).

## Lineage

### From

[Owner](Owner.md) + lazy [Pet](Pet.md) fetch — at construction:

<pre>
return OwnerSummaryResponse (<a href="../contracts/rest.md">HTTP</a>) { ...<a href="Owner.md">Owner</a> (<a href="../contracts/mysql.md">MySQL</a>), pets: <a href="Pet.md">Pet</a>[] (<a href="../contracts/mysql.md">MySQL</a>) }
</pre>

### To

None — returned to api-gateway over HTTP; not persisted or re-emitted.
