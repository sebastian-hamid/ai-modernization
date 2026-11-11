# Candidate WildFly interface inventory

KAN-15 / BG-06 source inventory, 11 November 2026. This maps the candidate application's network-facing interfaces, internal EJB/CDI and JNDI references, and the WildFly management/broker listeners relevant to startup seeding and schema migration. It is a source/config inventory supplemented by the KAN-18 runtime observations; it is not a BG-06 access-gate result.

## Network-facing application interfaces

| Interface | Entry/configuration | Authorization and internal path | BG-06 relationship |
| --- | --- | --- | --- |
| REST | `RestConfiguration` at `/rest`; `CargoMonitoringService` at `/cargo`, `HandlingReportService` at `/handling` and `/reports`, `GraphTraversalService` at `/graph-traversal` and `/shortest-path` | Calls the candidate REST/service layer. The current role and method outcomes are covered in the access matrices and capability receipts. | No path or call to `SampleDataGenerator` is present in this REST inventory. |
| Faces/servlets | WildFly Faces servlet at `*.xhtml`; `SessionServlet` at `/session`; `LegacyNavigationServlet` at nine exact aliases; local login/logout at `/login` and `/logout` | Candidate pages and servlet adapters; protected actions are evaluated in their capability-specific cases. `/admin/import.xhtml` is a separate staged handling-event import. | The import uses the BatchTrigger/BatchWorker path and does not call the sample generator or perform ORM DDL. |
| WebSocket | `/tracking` | `RealtimeCargoTrackingService`; source has no `@OnMessage` operation. | No startup, sample-data, or schema-migration operation is attached. |
| JAX-WS | No `@WebService`, `@WebServiceProvider`, or `webservices.xml` endpoint was found in candidate sources/configuration. | None. | No SOAP endpoint exposes startup or migration behavior. |
| HTTP remoting / remote naming / JMS HTTP connector | WildFly 42 HTTP listener at 8080; remote naming and Artemis HTTP connector both bind to this listener in the pinned `standalone-full.xml` | Remote lookup and connection start were tested with Reader, Operator, Administrator, anonymous, and invalid credentials. Valid application roles connected; anonymous/invalid were rejected. | This is a reachable protocol surface, but it exposes no remote EJB view for the startup generator. JMS destination send/consume authorization is separate and is covered by the BG-03/04/05 producer-boundary work, not by the connect-only probe. |

The application listener is published to the host only as `127.0.0.1:8082:8080`. PostgreSQL has no host-published port. The candidate does not declare a separate 4447 remoting socket binding in the pinned WildFly configuration; the HTTP remoting connector uses the Undertow default listener on 8080.

## Internal EJB, CDI, and JNDI references

The source contains no `@Remote` EJB view. REST resources, Faces/servlet adapters, startup beans, MDBs, and service classes call one another through CDI/EJB injection. The business interfaces `BookingService`, `CargoInspectionService`, `HandlingEventService`, and `RoutingService` are internal application service contracts; none is declared as a remote EJB interface.

The application JMS destinations are declared in `WEB-INF/web.xml` and consumed by these MDBs:

| JNDI name | Broker destination | Consumer / RunAs identity |
| --- | --- | --- |
| `java:app/jms/CargoHandledQueue` | `CargoHandledQueue` | `CargoHandledConsumer` / `InspectionWorker` |
| `java:app/jms/MisdirectedCargoQueue` | `MisdirectedCargoQueue` | `MisdirectedCargoConsumer` / `NotificationWorker` |
| `java:app/jms/DeliveredCargoQueue` | `DeliveredCargoQueue` | `DeliveredCargoConsumer` / `NotificationWorker` |
| `java:app/jms/RejectedRegistrationAttemptsQueue` | `RejectedRegistrationAttemptsQueue` | `RejectedRegistrationAttemptsConsumer` / `NotificationWorker` |
| `java:app/jms/HandlingEventRegistrationAttemptQueue` | `HandlingEventRegistrationAttemptQueue` | `HandlingEventRegistrationAttemptConsumer` / `HandlingWorker` |

Java producer references target four declared `java:app/jms` destinations: `HandlingEventRegistrationAttemptProducer` publishes handling attempts under `RunAs(HandlingAttemptProducer)`, and `JmsApplicationEvents` publishes cargo-handled, misdirected, and delivered events. No Java producer sends directly to the rejection queue. The broker's `deployment/wildfly/notification-disposition.cli` routes failed handling-attempt messages to `RejectedRegistrationAttemptsQueue`; after three failed deliveries there, broker dead-letter routing sends them to `DLQ`. This broker disposition is distinct from an application producer. Other explicit references include `java:app/configuration/GraphTraversalUrl` declared in `WEB-INF/web.xml`, `java:comp/DefaultManagedScheduledExecutorService` used by `SocketSessions`, and `java:jboss/datasources/CargoTrackerDS` in `persistence.xml`. WildFly's exported `jms/RemoteConnectionFactory` is provided by the base server configuration, not the application's own `java:app` declarations.

## WildFly listeners and observed reachability

A disposable peer attached only to the candidate-host-access network attempted TCP connections to the configured candidate and management/broker ports. It reached only 8080. The peer could not reach AJP 8009, HTTPS 8443, management HTTP/HTTPS 9990/9993, IIOP 3528/3529, transaction recovery/status 4712/4713, or native broker ports 5445/5455/5672/61616. The pinned WildFly config places the management interface on 127.0.0.1; the fixture also binds HTTPS and transaction sockets to the loopback `unsecure` interface. This is network reachability evidence, not an authentication test for an otherwise reachable listener.

## Seed and migration separation

`SampleDataGenerator` is a `@Singleton @Startup` bean; its `@PostConstruct` exits unless `lab.candidate.disposable=true`. Static source search found no other Java caller, REST/servlet mapping, remote EJB view, JMS destination, or user action that invokes it. Candidate `persistence.xml` sets schema-generation action to `none`. Flyway migration is run in the separate candidate migration profile using `schema_migrator`; KAN-18 evidence records server-observed migration identity, populated-row preservation, expected migration effects, application-role DDL denial, and unchanged startup/restart data snapshots.

These findings narrow the control-plane inventory but do not establish the required per-role denied-call/effect receipts for the four human BG-06 cases. Nor should the KAN-18 fixture checks alone be promoted as BG-06 gate results. All five BG-06 cases remain BLOCKED until a trusted gate adapter binds the required probes and independent effects to the specific BG-06 contracts.
