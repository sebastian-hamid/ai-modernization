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
- A source/config regression test inventories the candidate network and worker surface: JAX-RS base path rest with five path annotations mapped across three resources, SessionServlet (/session) and LegacyNavigationServlet (its nine legacy aliases) plus web.xml mappings for LocalLoginServlet (/login), LocalLogoutServlet (/logout), and FacesServlet (*.xhtml), WebSocket /tracking (no @OnMessage), five MDB consumers, startup beans SampleDataGenerator and BatchImportRequestService, no @Remote EJB view or timer annotations, and only the host-local app mapping 127.0.0.1:8082:8080. PostgreSQL has no published host port.
- Runtime JNDI, management-interface, broker reachability, role/session, and data/catalog effects still require separate checks; static inventory is not a security gate result.

## Evidence boundaries and next verification

The KAN-18 receipt now covers a populated synthetic V1 schema upgraded through V2/V3 under a server-observed schema_migrator identity. It verifies the exact five V2 indexes, preserves all seven table digests, exercises the legacy-sequence high-water branch (8000) and next generated ID (8001), checks V3 grants and protected migration-state denials, and confirms successful Reader/Operator/Administrator reads. Catalog, row, history, sequence, and privilege snapshots remain stable across app startup, all three reads, and restart. A disposable peer TCP probe could reach only the app/remoting listener on 8080; the management, HTTPS, IIOP, transaction, AJP, and direct broker listener ports were closed. JNDI/JMS share HTTP 8080, and this probe does not verify their protocol authorization. This remains supplemental machine/runtime evidence only. It does not establish the four human denials for sample seeding/reseed/ORM DDL; all five BG-06 gate cases remain BLOCKED.

Before any BG-06 case can pass:

1. Complete the static source inventory for JMS destinations/producers/consumers, CDI/EJB references, JNDI and management interfaces, and trace every reference/caller of SampleDataGenerator. Runtime-confirm that WildFly administration, EJB, and broker management interfaces are not reachable through the fixture networks.
2. Probe every actual control surface as anonymous, Reader, Operator, and Administrator. For the BG-06 seed/reseed/DDL behavior, distinguish the existing BG-01/BG-02 handling-event import route from any seed/schema operation; probe applicable routes and inspect/instrument the actual call graph. A guessed-path 404 alone is insufficient. Do not substitute the ordinary allowed GET /rest/cargo read for a denied mutation attempt.
3. Compare full application table content, schema/catalog, Flyway history, sequences, grants and ownership before/after startup, restart and denied probes. Use stable sanitized digests and explicit expected differences.
4. For the machine allow case, migrate a schema containing synthetic pre-existing rows through the supported Flyway upgrade path. Verify the server identity and exact scope, preserve full row digests, permit only the expected schema/history changes, and confirm the application role cannot perform DDL or edit migration state.

Five new static source/config regression checks and the existing 92 security unit tests pass (97 total). These checks document the inventory but do not prove runtime access denial or database effects. Until the remaining runtime checks and trusted gate adapter exist, all four human BG-06 cases and BG-06-MACHINE remain BLOCKED. Existing green KAN-18 checks must not be promoted into BG-06 PASS results.
