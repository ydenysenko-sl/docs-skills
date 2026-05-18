# MySQL

Relational store backing customers-service. Spring Data JPA over Hibernate; schema bootstrapped by Flyway. MySQL in container deploys, HSQLDB in dev. Connection settings come from config-server.

## petclinic.*

Single schema for owner / pet / pet_type entities.

### **Own** owners

One row per registered owner. Parent of `pets`.

Payload — [Owner](../objects/Owner.md):
- `id` — int (auto-increment) — PK
- `first_name`, `last_name` — varchar(30)
- `address` — varchar(255)
- `city` — varchar(80)
- `telephone` — varchar(20)

PK: `id`. No FKs into this table.

Migration: [V1__init.sql](https://github.com/spring-petclinic/spring-petclinic-microservices/blob/main/spring-petclinic-customers-service/src/main/resources/db/mysql/schema.sql).

#### Writers

[upsert-owner-and-pets](../flows/upsert-owner-and-pets.md) · [OwnerResource.java](https://github.com/spring-petclinic/spring-petclinic-microservices/blob/main/spring-petclinic-customers-service/src/main/java/org/springframework/samples/petclinic/customers/web/OwnerResource.java) — `POST /owners` / `PUT /owners/{id}`:

<pre>
on POST /owners:
  save <a href="../objects/Owner.md">Owner</a> (MySQL) { first_name, last_name, address, city, telephone }

on PUT /owners/{id}:
  load <a href="../objects/Owner.md">Owner</a> (MySQL) by id (404 if missing)
  apply patch fields
  save
</pre>

#### Readers

[GET /owners/{id}](rest.md) · [OwnerResource.java](https://github.com/spring-petclinic/spring-petclinic-microservices/blob/main/spring-petclinic-customers-service/src/main/java/org/springframework/samples/petclinic/customers/web/OwnerResource.java):

<pre>
on GET /owners/{id}:
  return load <a href="../objects/Owner.md">Owner</a> (MySQL) by id (404 if missing)
</pre>

### **Own** pets

One row per pet. Child of `owners`.

Payload — [Pet](../objects/Pet.md):
- `id` — int (auto-increment) — PK
- `name` — varchar(30)
- `birth_date` — date
- `type_id` — int — FK → `types(id)`
- `owner_id` — int — FK → `owners(id)`

PK: `id`. FKs: `type_id` → `types`, `owner_id` → `owners`. Index on `owner_id`.

#### Writers

[upsert-owner-and-pets](../flows/upsert-owner-and-pets.md) · [PetResource.java](https://github.com/spring-petclinic/spring-petclinic-microservices/blob/main/spring-petclinic-customers-service/src/main/java/org/springframework/samples/petclinic/customers/web/PetResource.java) — `POST /owners/{ownerId}/pets` / `PUT /owners/{ownerId}/pets/{petId}`:

<pre>
on POST /owners/{ownerId}/pets:
  owner ← load <a href="../objects/Owner.md">Owner</a> (MySQL) by ownerId (404 if missing)
  save <a href="../objects/Pet.md">Pet</a> (MySQL) { ...request, owner_id: owner.id }

on PUT /owners/{ownerId}/pets/{petId}:
  load <a href="../objects/Pet.md">Pet</a> (MySQL) by petId (404 if missing)
  apply patch fields
  save
</pre>

#### Readers

[OwnerSummaryResponse assembly](../objects/OwnerSummaryResponse.md) · [OwnerResource.java](https://github.com/spring-petclinic/spring-petclinic-microservices/blob/main/spring-petclinic-customers-service/src/main/java/org/springframework/samples/petclinic/customers/web/OwnerResource.java):

<pre>
on GET /owners/{id}:
  owner ← load <a href="../objects/Owner.md">Owner</a> (MySQL) by id
  pets  ← lazy-fetch owner.pets (one-to-many) — <a href="../objects/Pet.md">Pet</a> (MySQL)
</pre>

### **Own** types

Lookup table for pet species (`cat`, `dog`, `bird`, ...). Seeded by migration; not mutated at runtime.

Payload:
- `id` — int (auto-increment) — PK
- `name` — varchar(80)

#### Readers

[GET /petTypes](rest.md) · [PetResource.java](https://github.com/spring-petclinic/spring-petclinic-microservices/blob/main/spring-petclinic-customers-service/src/main/java/org/springframework/samples/petclinic/customers/web/PetResource.java):

<pre>
on GET /petTypes:
  return all rows from types (MySQL)
</pre>
