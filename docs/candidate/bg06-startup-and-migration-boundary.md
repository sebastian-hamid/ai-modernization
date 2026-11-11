# BG-06 startup and migration boundary

## Decision

BG-06 has two different security boundaries:

- **Human roles:** no application user, including Administrator, can trigger the demo sample generator, reseeding, or ORM schema creation. The candidate does expose a separate Administrator handling-event import UI at /admin/import.xhtml. That action flows through BatchImportView and BatchImportRequestService to a dedicated BatchTrigger/BatchWorker launcher; it imports staged events and is not a trigger for SampleDataGenerator or ORM DDL. Its authorization and data effects belong to the BG-01/BG-02 import cases. The four BG-06 human denial cases passed the fresh scoped gate described below.
- **Deployment identity:** BG-06-MACHINE authorizes Flyway schema migration only, executed as the server-verified schema_migrator database identity. It does not authorize sample-data loading or ORM schema generation.
- **Administrator import capability:** the existing /admin/import.xhtml action is the approved handling-event batch-import path. It is separate from BG-06 startup/migration; verify its authorization, worker identity, audit, and data effects under BG-01/BG-02.

## Current source facts

The complete mapped application, EJB/CDI/JNDI, JMS, and WildFly listener inventory is in [the interface inventory](wildfly-interface-inventory.md). It supplements the direct KAN-18 listener and protocol receipts but does not itself pass a BG-06 case.

- SampleDataGenerator is a @Singleton @Startup EJB with a @PostConstruct method. The method returns unless lab.candidate.disposable=true; the destructive sample-data behavior is therefore opt-in for the disposable historical baseline.
- The candidate persistence descriptor sets jakarta.persistence.schema-generation.database.action to none.
- No direct REST/JAX-RS or servlet mapping or other Java source caller invokes SampleDataGenerator in the candidate application; the only source references found are its own class and the provenance manifest.
- The candidate has an Administrator-facing /admin/import.xhtml handling-event batch trigger, disabled unless lab.import.enabled=true and delegated through BatchTrigger/BatchWorker identities. It is separate from startup sample seeding and database schema migration. This is the candidate implementation/crosswalk for the legacy BG-01/BG-02 import entries; the historical entry fields remain unchanged.
- A source/config regression test inventories the candidate network and worker surface: JAX-RS base path rest with five path annotations mapped across three resources, SessionServlet (/session) and LegacyNavigationServlet (its nine legacy aliases) plus web.xml mappings for LocalLoginServlet (/login), LocalLogoutServlet (/logout), and FacesServlet (*.xhtml), WebSocket /tracking (no @OnMessage), five MDB consumers, startup beans SampleDataGenerator and BatchImportRequestService, no @Remote EJB view or timer annotations, and only the host-local app mapping 127.0.0.1:8082:8080. PostgreSQL has no published host port.
- Runtime JNDI, management-interface, broker reachability, role/session, and data/catalog effects still require separate checks; static inventory is not a security gate result.

## Evidence boundaries and next verification

### Fresh scoped BG-06 verification — 11 November 2026

The fresh disposable BG-06 gate passed all five scoped cases: anonymous, Reader, Operator, and Administrator cannot invoke a seed/reseed/schema-DDL entry point, and deployment Flyway runs under the server-verified `schema_migrator` identity. The human checks combine the hashed Java/webapp/config inventory (including Facelets expressions), absence of callable generator/schema entry points, authenticated role identities, database-effect snapshots, and application-role DDL denials. The machine case verifies V1/V2/V3 against populated synthetic rows, the migration identity/effects, and separation from sample-data seeding/import. All owned resources and generated secrets were removed. See the [scoped validation receipt](../../notes/evidence/kan-15-bg06-scope/validation.json).

This scoped result does not refresh the aggregate current-capability gate or establish full KAN-15 completion. The remote JMS probe was connect/list-only: it sent and consumed no messages, so destination-level permissions are outside this receipt. The separate handling-event import remains under BG-01/BG-02.

The KAN-18 receipt covers a populated synthetic V1 schema upgraded through V2/V3 under a server-observed schema_migrator identity. It verifies the exact five V2 indexes, preserves all seven table digests, exercises the legacy-sequence high-water branch (8000) and next generated ID (8001), checks V3 grants and protected migration-state denials, and confirms successful Reader/Operator/Administrator reads. Catalog, row, history, sequence, and privilege snapshots remain stable across app startup, all three reads, and restart. A disposable peer TCP probe could reach only the app/remoting listener on 8080; the management, HTTPS, IIOP, transaction, AJP, and direct broker listener ports were closed. JNDI/JMS share HTTP 8080. A read-only protocol probe confirmed valid Reader/Operator/Administrator accounts can look up RemoteConnectionFactory and start a JMS connection, while anonymous and invalid credentials are rejected; it sent or consumed no messages. Destination-level send/consume authorization remains unverified. Those KAN-18 observations are supplemental; the separate fresh scoped BG-06 result above now passes its five cases.

The scoped BG-06 checks are complete for this candidate fixture. Follow-up verification is still required before full KAN-15 acceptance:

1. Extend identity/effect verification to every remaining KAN-15 human capability and machine worker case; the BG-06 result is specific to the seed/reseed/schema boundary.
2. Test JMS send/consume authorization at destination level under isolated fixtures. The BG-06 connect-only probe does not grant or prove any destination permission.
3. Refresh the aggregate current-capability gate from the latest scoped receipts while preserving the historical catalogue and separate RETIRED state.

The eight BG-06 static source/config regression checks pass. The independently reviewed fresh scoped gate passed 5/5 cases and persisted the relevant runtime, source, migration, and fixture hashes. This is a BG-06 scoped result, not a full KAN-15 result; the aggregate gate still needs a fresh refresh and remaining capability/retirement cases stay open.
