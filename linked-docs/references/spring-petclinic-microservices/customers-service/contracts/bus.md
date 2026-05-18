# Spring Cloud Bus

Async refresh fan-out over RabbitMQ. config-server publishes `RefreshRemoteApplicationEvent` on the bus when properties change; customers-service consumes and refreshes its `@RefreshScope` beans without restart.

## springCloudBus

Default Spring Cloud Bus exchange + queue on RabbitMQ. Topic exchange `springCloudBus`; per-instance auto-deleted queue.

### **Consume** RefreshRemoteApplicationEvent

Config-refresh signal. Carries the originating service id and destination filter.

Payload — [RefreshRemoteApplicationEvent](https://docs.spring.io/spring-cloud-bus/docs/current/api/org/springframework/cloud/bus/event/RefreshRemoteApplicationEvent.html):
- `originService` — string (e.g., `config-server:0:abc123`)
- `destinationService` — string (e.g., `customers-service:**` or `**`)
- `id` — string (event uuid)
- `timestamp` — long (epoch ms)

Routing: matched against `spring.cloud.bus.id`. Wildcard `**` fans out to every listener.

Consumed by [refresh-on-config-change](../flows/upsert-owner-and-pets.md) — auto-wired by `spring-cloud-starter-bus-amqp` at [pom.xml](https://github.com/spring-petclinic/spring-petclinic-microservices/blob/main/spring-petclinic-customers-service/pom.xml):

<pre>
on RefreshRemoteApplicationEvent (Bus):
  if destinationService matches "customers-service:**" or "**":
    pull new properties from config-server
    rebind @RefreshScope beans
</pre>

> No producer in customers-service — refresh originates from config-server (out of scope for this repo) when an operator hits its `/monitor` webhook.
