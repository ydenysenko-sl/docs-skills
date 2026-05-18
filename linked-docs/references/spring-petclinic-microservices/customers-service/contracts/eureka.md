# Eureka

Service discovery registration with the discovery-server. customers-service registers under `spring.application.name=customers-service`; api-gateway resolves it by name and load-balances across instances.

## customers-service

Registration entry advertised on the Eureka client heartbeat.

### **Register** customers-service

One entry per running instance.

Payload:
- `instanceId` — string (host:port:uuid)
- `app` — `CUSTOMERS-SERVICE`
- `ipAddr` — string
- `port` — int (default 8081)
- `homePageUrl` — `http://<host>:<port>/`
- `statusPageUrl` — `http://<host>:<port>/actuator/info`
- `healthCheckUrl` — `http://<host>:<port>/actuator/health`

Heartbeat: 30s renewal; 90s eviction.

Configured at [bootstrap.yml](https://github.com/spring-petclinic/spring-petclinic-microservices/blob/main/spring-petclinic-customers-service/src/main/resources/bootstrap.yml) · enabled by `@EnableDiscoveryClient` on [CustomersServiceApplication.java](https://github.com/spring-petclinic/spring-petclinic-microservices/blob/main/spring-petclinic-customers-service/src/main/java/org/springframework/samples/petclinic/customers/CustomersServiceApplication.java):

<pre>
on startup:
  register with discovery-server as "customers-service"
  publish health + info endpoints
  send heartbeat every 30s
</pre>

#### Consumers

api-gateway resolves `http://customers-service` via the registry and load-balances; visits-service does not call customers-service directly.

<pre>
api-gateway:
  GET http://customers-service/owners/{id}
  → resolve via Eureka → pick instance → HTTP
</pre>
