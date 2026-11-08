# Real Cargo Tracker candidate bootstrap — KAN-18 / KAN-15

Work in progress, 1 November 2026. The subsequent [browser workflow increment](../../docs/candidate/browser-workflows.md) enables cargo list/details/booking/destination pages; the [routing extension](../../docs/candidate/routing-workflow.md) adds secured sample route selection; full acceptance remains open. This module contains real application source ported from pinned Cargo Tracker, not the KAN-13 capability WAR or KAN-15 counter fixture. The original checkout, GlassFish service and synced sources remain read-only/unchanged. KAN-18 and KAN-15 remain In Progress; full intended functional/security acceptance is not met.

## Source and build

source-provenance.json records the original commit 57fc7b32d2597e43b5e0d454e707e0146de5258a and original file hashes from git archive of src/ and LICENSE. Candidate modifications are deliberate; original hashes are not current candidate hashes. Current execution input hashes are recorded under notes/evidence/kan-18-candidate/validation.json. The extra ten-case handling factory characterization test was copied from the repository's tests/java tree.

Pinned foundation: Java 25.0.5 / Jakarta EE 11 / standard WildFly 42 and the same immutable Maven/runtime digests used by KAN-13. Application dependencies: PrimeFaces 16.0.1 (current stable artifact from Maven Central checked 1 November), commons-lang3 3.20.0, JUnit 4.13.2; compiler 3.16.0, WAR 3.5.1, Surefire 3.5.4. Normal build requires candidate/security installed first. The disposable harness builds both in pinned containers.

Portability changes:
- Jakarta EE package migration; Java SE namespaces such as javax.naming retained.
- Standard Jakarta REST Application replaces Jersey ResourceConfig/MOXY registrations. JSON-P monitoring and JSON request handling are executed; route-client JSON/date mapping now has real loopback and browser coverage in the routing extension.
- Removed JAXB root annotations from the two JSON DTOs: JAXB is no longer part of the EE 11 API. XML representation compatibility is not claimed.
- PrimeFaces dashboard/widget and dialog/AJAX Java APIs adapted; old managed bean moved to CDI. Full rendered/mobile/flow/browser conversion remains KAN-19.
- Hibernate uses existing standard cascade/orphanRemoval rather than EclipseLink PrivateOwned; actual sample mappings and two handling effects tested. PostgreSQL mapping/schema migration is still KAN-21/22.
- Portable app-scoped JMS destination definitions replace GlassFish jmsra declarations. The first runtime accepted HTTP but worker delivery failed authorization. Added PermitAll only to internal MDB delivery methods while keeping RunAs HandlingWorker and role-restricted registration/inspection services. Broker/producer least-privilege verification remains incomplete.

## Functional/security increment

The application uses the reviewed candidate/security login/logout/CSRF components. The /session endpoint returns the authenticated user's own principal/roles/token. Tokens, passwords and cookies are not persisted in evidence.

Enabled operational routes:
- /rest/cargo: Reader, Operator, Administrator; real four-cargo data.
- /rest/handling/reports: Operator/Administrator with session CSRF, plus EJB roles.
- /login, /session and /logout support actual container local identities/session revocation.
- /admin/dashboard.xhtml and /admin/show.xhtml: Reader/Operator/Administrator.
- /admin/book.xhtml, /admin/changeDestination.xhtml and /admin/route.xhtml: Operator/Administrator with CSRF and facade/EJB roles.
- /rest/graph-traversal/shortest-path: Operator/Administrator sessions plus the separately scoped RoutingService internal account.

Only landing/About are public. **Other unported operational pages/callbacks and WebSocket and non-allowlisted assets are deliberately unavailable (404)** pending complete integration. Denying these routes does not satisfy authorized-workflow expectations. Booking/destination/list/details have the bounded Chromium coverage linked above. Controlled import/live updates and legacy mobile logger remain unavailable; full rendering/resource/mobile completeness is not claimed.

The HTTP role check rejects denied reports before the real submission bean; EJB annotations add a server-side service check. MDBs run under HandlingWorker, which no human test account receives. Full direct-call/role-escalation/broker/filesystem/session/WebSocket validation remains required; do not infer it from annotation declarations.

## Disposable verification and safeguards

    python3 tests/candidate-runtime/run_candidate.py
    python3 -m unittest discover -s tests/candidate-runtime -p test_harness.py -v

Run in /home/yasinrdp/projects/ai-modernization under WSL. Only selected library/candidate/test inputs are copied into .work/kan18/context-* (fresh for every run). The harness refuses an existing task container/private files, generates private per-run ApplicationRealm digests, binds a Docker-selected loopback port and removes only its created container plus private files. Log/removal failures cannot skip credential cleanup/reporting. No historical service or DB volume is reused.

The **default application descriptor** uses a separately provisioned CargoTrackerDS and schema action none; no deployed schema migration is implemented. Sample generation returns without action unless lab.candidate.disposable is explicitly set. The former periodic filesystem scanner is removed. Handling-event imports can only be started through the Administrator page after the batch worker is configured; the import kill switch remains disabled unless lab.import.enabled is explicitly set. Staged files and generated outputs use fixed private directories.

The **test-only image** overlays persistence-lab.xml using isolated in-memory ExampleDS/H2 and drop-and-create. It requires DISPOSABLE_CANDIDATE_LAB=true and sets the seed flag; it is not a production image. Do not use it with retained/real data. Restart/recovery, durable storage, Flyway and PostgreSQL acceptance remain later work.

The current harness checks35 domain cases (bootstrap evidence originally had34) (one original empty TODO retained), server principal/role/session rotation, Reader/anonymous handling denials and Operator CSRF, reads for all three roles, actual Operator and Administrator asynchronous persisted cargo changes and logout cookie replay. Three mocked harness tests cover partial-secret initialization and Docker log/removal failures. It checks unchanged monitoring state after denied requests, but **does not establish independent database/queue/business-audit absence**; KAN-14 remains blocked and no global security pass is claimed.

## Next integration work

Complete remaining page/action/browser workflows, controlled batch/worker ACLs, live WebSocket logout/expiry behavior and independent side-effect observers. Expand real candidate adapters, then execute KAN-14 desired cases. Keep the two synthetic fixture results separate from this application's evidence. Both KAN-15 and KAN-18 stay open until their full acceptance is verified.

References: [WildFly 42 developer guide](https://docs.wildfly.org/42/Developer_Guide.html), [PrimeFaces 16 migration](https://github.com/primefaces/primefaces/blob/master/docs/migrationguide/16_0_0.md), [official artifact metadata](https://repo.maven.apache.org/maven2/org/primefaces/primefaces/maven-metadata.xml).


## Subsequent live UI increment

The authenticated [live tracking view](../../docs/candidate/live-tracking-ui.md) now provides actual rows/markers and session-end clearing. Earlier disabled-map/live-UI statements are historical; the raw legacy map client remains blocked. KAN-19 still requires the mobile event logger. KAN-17 endpoint work is Done in Jira.

## Subsequent mobile workflow increment

The [responsive handling form](../../docs/candidate/mobile-handling.md) now replaces the legacy mobile flow for supported handling work. Earlier mobile-disabled/pending statements describe prior checkpoints. Full platform/security/resilience acceptance remains separate.
