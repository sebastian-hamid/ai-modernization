# BG-06 startup and migration boundary

## Decision

BG-06 has two different security boundaries:

- **Human roles:** no application user, including Administrator, can trigger the demo sample generator, reseeding, or ORM schema creation. The candidate does expose a separate Administrator handling-event import UI at /admin/import.xhtml. That action flows through BatchImportView and BatchImportRequestService to a dedicated BatchTrigger/BatchWorker launcher; it imports staged events and is not a trigger for SampleDataGenerator or ORM DDL. Its authorization and data effects belong to the BG-01/BG-02 import cases. The four BG-06 human cases remain denial cases for sample reseed/schema-DDL and stay BLOCKED until exhaustive entry-point inventory and direct-access/effect evidence establish that boundary.
- **Deployment identity:** BG-06-MACHINE authorizes Flyway schema migration only, executed as the server-verified schema_migrator database identity. It does not authorize sample-data loading or ORM schema generation.
- **Administrator import capability:** the existing /admin/import.xhtml action is the approved handling-event batch-import path. It is separate from BG-06 startup/migration; verify its authorization, worker identity, audit, and data effects under BG-01/BG-02.

## Current source facts

- SampleDataGenerator is a @Singleton @Startup EJB with a @PostConstruct method. The method returns unless lab.candidate.disposable=true; the destructive sample-data behavior is therefore opt-in for the disposable historical baseline.
- The candidate persistence descriptor sets jakarta.persistence.schema-generation.database.action to none.
- No direct REST/JAX-RS or servlet mapping or other Java source caller invokes SampleDataGenerator in the candidate application; the only source references found are its own class and the provenance manifest.
- The candidate has an Administrator-facing /admin/import.xhtml handling-event batch trigger, disabled unless lab.import.enabled=true and delegated through BatchTrigger/BatchWorker identities. It is separate from startup sample seeding and database schema migration. This is the candidate implementation/crosswalk for the legacy BG-01/BG-02 import entries; the historical entry fields remain unchanged.
- Candidate application API/servlet mappings still need a complete reviewed inventory, including EJB views, CDI references, timers/schedulers, JNDI, and management reachability.

## Evidence boundaries and next verification

The KAN-18 receipt proves fresh V1/V2/V3 migration with a separate schema_migrator, denies DDL and Flyway-history mutation to cargo_app, and shows unchanged seven-table content digests across normal startup, three human read-only sessions, and restart. It is supplemental evidence; it is not a BG-06 gate result.

Before any BG-06 case can pass:

1. Inventory all candidate JAX-RS resources/methods, servlet mappings, WebSocket endpoints, JMS destinations/producers/consumers and broker-facing trigger paths, EJB business/remote views, CDI/EJB references, startup hooks, timers/schedulers, JNDI and management interfaces. Confirm the fixture publishes no WildFly administration, EJB, or broker management port. Trace every reference/caller of SampleDataGenerator.
2. Probe every actual control surface as anonymous, Reader, Operator, and Administrator. For the BG-06 seed/reseed/DDL behavior, distinguish the existing BG-01/BG-02 handling-event import route from any seed/schema operation; probe applicable routes and inspect/instrument the actual call graph. A guessed-path 404 alone is insufficient. Do not substitute the ordinary allowed GET /rest/cargo read for a denied mutation attempt.
3. Compare full application table content, schema/catalog, Flyway history, sequences, grants and ownership before/after startup, restart and denied probes. Use stable sanitized digests and explicit expected differences.
4. For the machine allow case, migrate a schema containing synthetic pre-existing rows through the supported Flyway upgrade path. Verify the server identity and exact scope, preserve full row digests, permit only the expected schema/history changes, and confirm the application role cannot perform DDL or edit migration state.

Until these checks and the trusted gate adapter exist, all four human BG-06 cases and BG-06-MACHINE remain BLOCKED. Existing green KAN-18 checks must not be promoted into BG-06 PASS results.
