# REST

HTTP endpoints customers-service serves to api-gateway and other internal callers. JSON over HTTP; service registered with Eureka and reachable as `http://customers-service/...` through the gateway. No app-level auth — network boundary only.

## /owners/*

Owner CRUD + nested pet writes. All endpoints return JSON.

### **Serve** POST /owners

Create a new owner.

Request — inline:
- `firstName`, `lastName` — string (required)
- `address`, `city`, `telephone` — string (required)

Response — [Owner](../objects/Owner.md) (201 Created):
- `id` — int
- `firstName`, `lastName`, `address`, `city`, `telephone` — string

[upsert-owner-and-pets](../flows/upsert-owner-and-pets.md) · [OwnerResource.java](https://github.com/spring-petclinic/spring-petclinic-microservices/blob/main/spring-petclinic-customers-service/src/main/java/org/springframework/samples/petclinic/customers/web/OwnerResource.java):

<pre>
on POST /owners:
  save <a href="../objects/Owner.md">Owner</a> (<a href="mysql.md">MySQL</a>) { ...request }
  return saved <a href="../objects/Owner.md">Owner</a> (<a href="mysql.md">MySQL</a>)
</pre>

### **Serve** GET /owners/{id}

Read one owner with embedded pets.

Request: path param `id` (int).

Response — [OwnerSummaryResponse](../objects/OwnerSummaryResponse.md):
- `id`, `firstName`, `lastName`, `address`, `city`, `telephone`
- `pets` — array of `{ id, name, birthDate, type }`

Errors: `404` if `id` unknown.

[GET owner](../objects/OwnerSummaryResponse.md) · [OwnerResource.java](https://github.com/spring-petclinic/spring-petclinic-microservices/blob/main/spring-petclinic-customers-service/src/main/java/org/springframework/samples/petclinic/customers/web/OwnerResource.java):

<pre>
on GET /owners/{id}:
  owner ← load <a href="../objects/Owner.md">Owner</a> (<a href="mysql.md">MySQL</a>) by id (404 if missing)
  return <a href="../objects/OwnerSummaryResponse.md">OwnerSummaryResponse</a> (HTTP) { ...<a href="../objects/Owner.md">Owner</a> (<a href="mysql.md">MySQL</a>), pets: owner.pets }
</pre>

### **Serve** PUT /owners/{id}

Patch an existing owner.

Request: path param `id`; body fields same as POST.

Response: `204 No Content`.

Errors: `404` if `id` unknown.

[upsert-owner-and-pets](../flows/upsert-owner-and-pets.md) · [OwnerResource.java](https://github.com/spring-petclinic/spring-petclinic-microservices/blob/main/spring-petclinic-customers-service/src/main/java/org/springframework/samples/petclinic/customers/web/OwnerResource.java):

<pre>
on PUT /owners/{id}:
  owner ← load <a href="../objects/Owner.md">Owner</a> (<a href="mysql.md">MySQL</a>) by id (404 if missing)
  apply patch fields
  save
</pre>

### **Serve** POST /owners/{ownerId}/pets

Add a pet under an owner.

Request: path param `ownerId`; body `{ name, birthDate, typeId }`.

Response — [Pet](../objects/Pet.md) (201 Created).

Errors: `404` if `ownerId` unknown; `400` if `typeId` invalid.

[upsert-owner-and-pets](../flows/upsert-owner-and-pets.md) · [PetResource.java](https://github.com/spring-petclinic/spring-petclinic-microservices/blob/main/spring-petclinic-customers-service/src/main/java/org/springframework/samples/petclinic/customers/web/PetResource.java):

<pre>
on POST /owners/{ownerId}/pets:
  owner ← load <a href="../objects/Owner.md">Owner</a> (<a href="mysql.md">MySQL</a>) by ownerId (404 if missing)
  save <a href="../objects/Pet.md">Pet</a> (<a href="mysql.md">MySQL</a>) { ...request, owner_id: owner.id }
</pre>

### **Serve** PUT /owners/{ownerId}/pets/{petId}

Patch an existing pet.

Request: path params; body `{ name, birthDate, typeId }`.

Response: `204 No Content`.

Errors: `404` if `petId` unknown.

### **Serve** GET /petTypes

Lookup pet species.

Request: none.

Response: array of `{ id, name }`.

[PetResource.java](https://github.com/spring-petclinic/spring-petclinic-microservices/blob/main/spring-petclinic-customers-service/src/main/java/org/springframework/samples/petclinic/customers/web/PetResource.java):

<pre>
on GET /petTypes:
  return all rows from types (<a href="mysql.md">MySQL</a>)
</pre>
