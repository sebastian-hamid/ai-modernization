# BG-06 startup and migration boundary

## Decision

BG-06 has two different security boundaries:

- **Human roles:** no application user, including Administrator, can trigger the demo sample generator, reseeding, or ORM schema creation. The current candidate exposes no such control-plane feature. The four human cases remain denial cases and stay BLOCKED until an exhaustive entry-point inventory and direct-access/effect evidence are available.
- **Deployment identity:** BG-06-MACHINE authorizes Flyway schema migration only, executed as the server-verified schema_migrator database identity. It does not authorize sample-data loading or ORM schema generation.
- **Future controlled import:** policy permits Administrator to initiate an approved controlled batch/import feature. That capability is separate from BG-06 startup/migration and needs its own endpoint, authorization, worker identity, audit, and data-effect cases when implemented.

## Current source facts

- SampleDataGenerator is a @Singleton @Startup EJB with a @PostConstruct method. The method returns unless lab.candidate.disposable=true; the destructive sample-data behavior is therefore opt-in for the disposable historical baseline.
- The candidate persistence descriptor sets jakarta.persistence.schema-generation.database.action to none.
- No direct REST/servlet mapping or other source caller of SampleDataGenerator was found in the candidate application.
- Candidate application API/servlet mappings still need a complete reviewed inventory, including EJB views, CDI references, timers/schedulers, JNDI, and management reachability.

## Evidence boundaries and next verification

The KAN-18 receipt proves fresh V1/V2/V3 migration with a separate schema_migrator, denies DDL and Flyway-history mutation to cargo_app, and shows unchanged seven-table content digests across normal startup, three human read-only sessions, and restart. It is supplemental evidence; it is not a BG-06 gate result.

Before any BG-06 case can pass:

1. Inventory all candidate JAX-RS resources/methods, servlet mappings, WebSocket endpoints, JMS destinations/producers/consumers and broker-facing trigger paths, EJB business/remote views, CDI/EJB references, startup hooks, timers/schedulers, JNDI and management interfaces. Confirm the fixture publishes no WildFly administration, EJB, or broker management port. Trace every reference/caller of SampleDataGenerator.
2. Probe every actual control surface as anonymous, Reader, Operator, and Administrator. If no trigger surface exists, combine the full inventory with direct probes of all exposed interfaces/configured management endpoints and a guessed-path bypass check. Do not substitute the ordinary allowed GET /rest/cargo read for a denied mutation attempt.
3. Compare full application table content, schema/catalog, Flyway history, sequences, grants and ownership before/after startup, restart and denied probes. Use stable sanitized digests and explicit expected differences.
4. For the machine allow case, migrate a schema containing synthetic pre-existing rows through the supported Flyway upgrade path. Verify the server identity and exact scope, preserve full row digests, permit only the expected schema/history changes, and confirm the application role cannot perform DDL or edit migration state.

Until these checks and the trusted gate adapter exist, all four human BG-06 cases and BG-06-MACHINE remain BLOCKED. Existing green KAN-18 checks must not be promoted into BG-06 PASS results.
