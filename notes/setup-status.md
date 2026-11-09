# Setup status
Verified 23 October 2026 (Europe/Bratislava). Checks ran on the actual WSL host, not the synced ChatGPT sources.

## Working
| Area | Evidence |
| --- | --- |
| WSL | Ubuntu-24.04 running as WSL version 2; Ubuntu 24.04.5 LTS; user yasinrdp. |
| Java | OpenJDK and javac 21.0.12.1. JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64. |
| Maven | Ubuntu Maven 3.8.7 at /usr/bin/mvn, home /usr/share/maven, uses Java 21. Verified fresh login and interactive shells. |
| Git | WSL host Git 2.43.0; isolated Jenkins candidate agent Git 2.53.0; repository main at 92ebf5e169d775acd8756fe6854d0eab68972a2f after KAN-29. |
| GitHub | origin is https://github.com/sebastian-hamid/ai-modernization.git; public main contains reviewed commit 92ebf5e169d775acd8756fe6854d0eab68972a2f. |
| Docker | Client/Engine 29.9.1, Docker Desktop 4.96.0; Compose v5.6.0. hello-world completed successfully. |
| Jenkins | Existing ai-modernization-jenkins container up, image jenkins/jenkins:lts-jdk21, version marker 2.580.1. Login endpoint returned HTTP 200 from Windows and Ubuntu. |
| Jenkins security | useSecurity=true; local user database; authenticated full-control authorization. Existing account record named jenkinsadmin. Configured URL http://localhost:8080/. |
| Jenkins storage | Existing Compose publishes 127.0.0.1:8080 and persists /var/jenkins_home in a named volume. Configuration was preserved. |

## Fixes applied
- Installed Ubuntu's maven package. Previously Maven resolved to /mnt/c/ProgramDev/apache-maven-3.9.11/bin/mvn; the Windows installation is unchanged.
- Added ~/.config/ai-modernization/java-env.sh and sourced it from ~/.profile and ~/.bashrc. This addresses JAVA_HOME in both login automation and interactive shells. Non-login scripts should source that file explicitly.
- Backed up shell files as ~/.profile.before-ai-modernization-20261023 and ~/.bashrc.before-ai-modernization-20261023.
- Added project .gitignore for experiments/, .work/, target directories and common secrets. Existing upstream checkout was neither deleted nor imported.
- Preserved docs/ and specifications/ instead of renaming them to match a proposed layout.
- Added baseline notes, logs and reproduction script. Reviewed setup and CI changes are versioned and published on GitHub; synced references remain untouched.

## Verified Jenkins operations
Authenticated Jenkins administrator sign-in and controller restart persistence were verified. The candidate node now uses the rotated identity ai-modernization-candidate-secure (label unchanged); its replacement secret is stored at mode 600 in ignored .work. The agent reconnected over WebSocket and post-rotation build #5 passed.

## Remaining limitation
The Jenkins Declarative linter endpoint returned HTTP 403 for anonymous access. Build #3 and post-rotation build #5 loaded the Pipeline from SCM and passed; authenticated UI access is confirmed, while API token access was not configured.

## Other verified baseline results
Legacy packaging and domain tests now PASS after historical dependency recovery; see [legacy-baseline.md](legacy-baseline.md). Runtime and booking integration now PASS: GlassFish 4.1 with the documented HK2-277 metadata correction, embedded Derby/JMS, four Arquillian booking tests, and HTTP tracking/routing/handling checks. See [legacy-runtime.md](legacy-runtime.md). The isolated Jenkins baseline pipeline also passes; see [jenkins-baseline.md](jenkins-baseline.md).

## Useful verification commands
Run in a fresh Ubuntu shell:
    printenv JAVA_HOME
    command -v mvn
    java -version
    javac -version
    mvn -version
    cd /home/yasinrdp/projects/ai-modernization
    git status
    git ls-remote origin refs/heads/main
    docker compose -f infrastructure/compose.yaml ps

Do not use docker compose down -v: that would delete Jenkins data.

## Baseline recovery completed
A fresh source export built cargo-tracker.war successfully in the pinned Java 8/Maven container. Five domain test classes passed: 24 reported tests, zero failures/errors/skips; ItineraryTest.testNextExpectedEvent is an empty TODO.
Eclipse artifacts were recovered from their original publisher's HTTPS repository. The missing PrimeFaces theme and its build plugin were rebuilt from exact official release tags; published-binary equality is unverified. Application source, dependency versions and the upstream checkout are unchanged. A separate test POM changes only skipTests to false.
The recovery script, settings, provenance hashes and reports are in infrastructure/ and notes/evidence/. Runtime milestone is now complete on host port 8081; see legacy-runtime.md. The isolated Jenkins baseline pipeline and candidate SCM pipeline pass; see jenkins-baseline.md and notes/evidence/kan-29-jenkins-candidate/summary.json. Broader behavior characterization remains next.

## Runtime milestone completed
The application is healthy at http://localhost:8081/cargo-tracker/. Four booking integration tests and tracking/routing/asynchronous-handling HTTP checks passed against the Compose-managed runtime. Original GlassFish deployment failure, the module-metadata correction and remaining coverage gaps are documented in [legacy-runtime.md](legacy-runtime.md).

## Jenkins milestone completed
Build 1 of ai-modernization-baseline finished SUCCESS in 99.495 seconds. It published 28 reported tests (24 domain + four booking; one empty TODO), passed HTTP workflow checks and archived the WAR/provenance. A separate non-root Java 21/Java 8 agent runs all builds; controller executors are zero. Source mode remains a local snapshot. The candidate SCM pipeline now passes build 3 on reviewed commit 92ebf5e; see [jenkins-baseline.md](jenkins-baseline.md) and the KAN-29 evidence. The historical baseline job was preserved.

## Expanded handling coverage (26 October 2026)
See [handling-characterization.md](handling-characterization.md) for added factory and live workflow coverage, observed legacy defects, test counts and fixture limits. Jenkins restart and agent reconnection have now been exercised; interactive administrator login remains unverified.

Jenkins build 4: SUCCESS; 53 application cases and 10 tooling checks passed. See [build evidence](evidence/jenkins-build-4/summary.json). Remaining blockers include interactive Jenkins login verification, GitHub publication/SCM wiring, final JMS retry disposition, and disposable GlassFish restart recovery.

## Coverage/access review (27 October 2026)
Jenkins build 6 passed: 134 application cases and 10 tooling checks, including 81 new entrypoint contracts. The separate access-control requirement FAILED: anonymous data reads, handling writes and cross-origin WebSocket access are confirmed. See [coverage matrix, findings and remaining gaps](test-coverage-review.md). Production source and shared demo were preserved.

## Baseline documentation (28 October 2026)
Functional, architecture and technical baseline documents are available in [docs/baseline](../docs/baseline/README.md). This pass verified source references and archived evidence, not current service health or target compatibility.

## Candidate checkpoint — 1 November 2026

The earlier publication-pending entries above are historical. Repository main has been published to GitHub; KAN-20 was independently reviewed and pushed as e467875. The shared historical app currently returns HTTP200 at localhost8081; Jenkins and its build agent are preserved.

The separate disposable candidate uses pinned Java25/JakartaEE11/WildFly42, not the Ubuntu host's baseline Java21 configuration. Current browser/runtime evidence is under notes/evidence/kan-20-navigation and notes/evidence/kan-15-effects. The candidate fixture is removed after verification; this is not an always-running or production deployment.

KAN-15 now has a bounded independent SQL/broker/invocation observer and fresh handling-denial/revocation catalogue adapter; see ../docs/candidate/independent-effects.md. Full security/platform acceptance and PostgreSQL/Flyway migration remain incomplete. Interactive Jenkins administrator login is still not newly verified by these candidate tests.

## Candidate update — 2 November 2026 (KAN-26)

The disposable candidate passed 367 application / 348 browser checks and 35 reported domain cases (one inherited empty TODO), including the 90-second WebSocket closure fix, abrupt peer-reset isolation, unrelated cargo persistence and all-role session revocation. Independent reviewer /root/review_kan26_disconnect approved the changes and independently ran all 54 tooling checks. This does not reverify every historical host setup claim above. Shared historical runtime/Jenkins remain preserved; complete access coverage is still 256 PASS / 246 BLOCKED. Details: [disconnect regression](../docs/candidate/disconnect-regression.md).

## Access coverage update — 2 November 2026 (KAN-15)

Six modern navigation mappings now have24active-actor proofs. Fresh367application/417browser/35reported domain cases PASS(one inherited emptyTODO),60toolingchecksPASS. Catalogue280PASS/222BLOCKED, full KAN-15 incomplete. See [navigation action matrix](../docs/candidate/navigation-action-matrix.md). Task resources/private files removed; original host setup claims are not rerun by this increment.

## Latest access checkpoint — 2 November 2026 (KAN-15 routed details)

ACTION-14 adds four verified routed-list detail cases: native roles click the exact cargo link and verify its ID/routing/transport status; anonymous direct access denies before data disclosure. Fresh367application/431browser/35reported domain cases PASS(one inherited emptyTODO),61toolingchecksPASS. Current catalogue284PASS/218BLOCKED, full KAN-15 incomplete. Task cleanup passed; see [action handoff](kan15-action-handoff.md) for remaining effect-observer and callback-method gaps.

## Latest access checkpoint — 2 November 2026 (KAN-15 booking)

ACTION-29 now has eight actual POST/role/logout/expiry proofs with independent per-request SQL/queue/audit observations. Permitted booking has real unique cargo/Reader deadline readback, one bookNewCargo invocation and no JMS expectation. Fresh411application/431browser/35reported domain cases PASS(one inherited emptyTODO),68tooling checks PASS; catalogue292PASS/210BLOCKED/nativeexit2. Full KAN-15 remains incomplete. The authoritative generator preserves explicit POST for five mutation callbacks. Task resources/private files removed; see [booking matrix](../docs/candidate/booking-action-matrix.md) and [action handoff](kan15-action-handoff.md).

## Latest access checkpoint — 2 November 2026 (KAN-15 destination change)

ACTION-09 adds eight actual POST/role/logout/expiry proofs with independent per-request SQL/queue/audit observations. O/A change only their own booking-control cargo FIHEL→USNYC, preserving ID/origin/deadline/state and all other cargos; exactly one destination invocation and no JMS are required. Fresh 442 application / 431 browser / 35 reported domain cases PASS (one inherited empty TODO), 72 tooling checks PASS; catalogue 300 PASS / 202 BLOCKED, native exit 2. Full KAN-15 remains incomplete; see the [destination matrix](../docs/candidate/destination-action-matrix.md). Task resources/private files removed; historical runtime/source and shared services preserved.

## Latest access checkpoint — 2 November 2026 (KAN-15 route actions)

ACTION-17/ACTION-19 add sixteen actual POST/role/logout/expiry proofs with per-request independent observations and explicit alias traceability. O/A initial assignment and genuinely different replacement persist the exact chosen itinerary, preserving other cargo state and deadline; SQL change, one assignment invocation and no JMS required. Fresh 523 application / 431 browser / 35 reported domain cases PASS (one inherited empty TODO), 77 tooling checks PASS. Catalogue 316 PASS / 186 BLOCKED, native exit 2; full KAN-15 incomplete. Task resources/private files removed; historical source/runtime/shared services preserved. See [routing matrix](../docs/candidate/routing-action-matrix.md).

## Latest access checkpoint — 2 November 2026 (KAN-15 handling and user decision)

All40 inventoried write-action/role/logout/expiry cases now pass. ACTION-41 uses actual Faces submission, unchanged per-denial SQL/queue/audit samples, real accepted status plus core JMS add/ack/registration/inspection counters and Reader IN_PORT/location/deadline readback. Fresh565application/431browser/35reported domain cases PASS(one inherited emptyTODO),81tooling checks PASS; catalogue324PASS/178BLOCKED, nativeexit2. Full KAN-15 incomplete:132read-only callbacks and46internal/worker cases remain. Task resources/private files removed; historical source/runtime/shared services preserved. User approved current-UI acceptance proposal; implementation/conditional retirement stillpending. See [decision](decisions/2026-11-02-current-ui-acceptance.md) and [handling matrix](../docs/candidate/handling-action-matrix.md).

## Latest access checkpoint — 2 November 2026 (KAN-15 current gate)

The first fresh v2 gate reports 308 PASS / 162 BLOCKED across 470 current cases; all 76 retirement checks remain BLOCKED. The same fixture preserves the historical 502-case audit at 324 PASS / 178 BLOCKED. Native 565 checks and Chromium 431 checks passed; cleanup passed and shared services remain running. Independent original-file/hash inspection and all 54 security unit tests now pass, resolving the earlier reviewer-access limitation. Current source-proof gaps deliberately block all 16 booking/destination cases; full acceptance remains incomplete. See [current gate checkpoint](../docs/candidate/current-capability-gate.md).

## Latest access checkpoint — 3 November 2026 (KAN-15 source entries)

Actual booking source GETs and selected-cargo details-to-editor link navigation now support all16booking/destination role/session cases in the current gate. Current324PASS/146BLOCKED; historical502audit324PASS/178BLOCKED;76retirementchecksBLOCKED. Native565/Chromium431checksPASS;32fixture+54securityunit testsPASS. Source policy, application code and historical contracts unchanged. Fresh owned resource/private cleanup passed; shared services preserved. See [source-entry evidence](../docs/candidate/source-entry-evidence.md).

## Latest access checkpoint — 3 November 2026 (KAN-15 current loads)

ACTION07/ACTION20 add eight current GET actor cases with independent selected-cargo values, distinct destination controls and24missing/malformed/unknown-ID checks. Current332PASS/138BLOCKED; historical502audit324PASS/178BLOCKED; retirement76BLOCKED. Native603/browser431PASS;36fixture+56securityunitsPASS. Two early failed fixture attempts were cleaned up; a bounded compiled-getter diagnostic established trailing location-name whitespace and the exact visible-name comparison now passes. Owned/private cleanup passed; shared services preserved. See [current load evidence](../docs/candidate/current-load-behaviors.md).

## Access checkpoint — 4 November 2026 (KAN-15 route choices)

[Route choices and itinerary alias](../docs/candidate/current-route-choices.md): eight current cases pass, including real route choices, selected cargo binding, exact alias redirect/denial, and 24 invalid-ID cases. Current 340/130, historical 324/178, retirement 76 BLOCKED. 650 native, 431 browser and 95 unit checks passed; owned cleanup passed and shared services stayed up.

The ACTION-15 [route cargo details checkpoint](../docs/candidate/current-route-choices.md#selected-cargo-details) passed four more current cases. The fixture passed 652 native and 431 browser checks, with owned cleanup verified.

The [ACTION-10 claimed cargo checkpoint](../docs/candidate/current-claimed-cargo.md) verified four current actor cases and owned cleanup. The current gate is 348 PASS and 122 BLOCKED.

The [cargo entry checkpoint](../docs/candidate/current-cargo-entries.md) passed 16 current cases, 652 native and 507 browser checks and owned cleanup. Current coverage is 364 PASS / 106 BLOCKED.

The [return and tracking checkpoint](../docs/candidate/current-return-and-tracking.md) passed 16 current cases, 661 native and 555 browser checks, with owned cleanup verified. Current coverage is 380 PASS / 90 BLOCKED.

The [initial replacement checkpoint](../docs/candidate/replacement-capabilities.md) passed 12 cases with independent cancellation snapshots and owned cleanup. Current coverage is 392 PASS / 78 BLOCKED.

The [booking replacement checkpoint](../docs/candidate/booking-replacement-capabilities.md) passed eight role cases with invalid-deadline no-change snapshots and positive booking POST, database, and independent readback evidence. The fresh fixture passed 661 native and 669 browser checks, with owned cleanup verified. Current coverage is 400 PASS / 70 BLOCKED. All 76 retirement checks remain BLOCKED.

The [handling single-page checkpoint](../docs/candidate/handling-single-page.md) passed four role cases against the real mobile handling page. The fresh fixture passed 661 native and 703 browser checks, with owned cleanup verified. Current coverage is 404 PASS / 66 BLOCKED. Remaining current blocks are 20 replacement and 46 internal cases. All 76 retirement checks remain BLOCKED. Evidence: [validation](evidence/kan-15-handling-single-page/validation.json).


The [handling cargo and voyage checkpoint](../docs/candidate/handling-cargo-voyage.md) passed four role cases. Operator and Administrator had valid cargo/voyage choices; invalid cargo and voyage values and missing voyages for both LOAD and UNLOAD were rejected. The fresh fixture passed 661 native and 725 browser checks with owned cleanup verified. Current coverage is 408 PASS / 62 BLOCKED, leaving 16 replacement and 46 internal cases. All 76 retirement cases remain BLOCKED. Evidence: [validation](evidence/kan-15-handling-cargo-voyage/validation.json).

The [handling location checkpoint](../docs/candidate/handling-location.md) passed four role cases. Operator and Administrator selected a valid location. Missing and forged location values were rejected by the real server form with unchanged database and queue effects. The fixture passed 661 native and 749 browser checks with owned cleanup verified. Current coverage is 412 PASS / 58 BLOCKED, leaving 12 replacement and 46 internal cases. All 76 retirement cases remain BLOCKED. Evidence: [validation](evidence/kan-15-handling-location/validation.json).
## Latest access checkpoint — 8 November 2026 (KAN-15 handling event)

ACTION-38 now verifies current event enum behavior, invalid event rejection, required voyages for LOAD/UNLOAD, and exact persisted CUSTOMS rows with null voyage association. All four actor cases passed using real browser form submissions and a bounded read-only fixture observer. The SQL DATE mapping is reflected in the assertion: persistence records the calendar date at midnight. Fresh fixture: 661 native and 779 browser checks; owned cleanup passed. Current gate is 416 PASS / 54 BLOCKED; historical audit 324 PASS / 178 BLOCKED; all 76 retirement checks remain BLOCKED. Two earlier fixture attempts were not promoted: attempt 1 timed out waiting for the handling-event Operator-after effects snapshot (472 browser checks), and attempt 2 rejected the browser-created cargo ID at an over-restrictive observer guard. Both completed cleanup; only the corrected run is promoted. Independent runtime/publication review is pending. See [handling-event evidence](../docs/candidate/handling-event.md) and [sanitized validation](evidence/kan-15-handling-event/validation.json).

## Latest access checkpoint — 8 November 2026 (KAN-15 handling voyage)

ACTION-39 now verifies the known 0100S option and selection, forged voyage rejection, required voyages for LOAD/UNLOAD, and same-cargo non-load voyage clearing. Its promoted proof explicitly composes the real voyage-control interval with the same-fixture ACTION-38 CUSTOMS positive control; no second event submission is claimed. All four actor cases passed. The fixture passed 661 native and 791 browser checks with owned cleanup. Current gate is 420 PASS / 50 BLOCKED; historical audit 324 PASS / 178 BLOCKED; all 76 retirement checks remain BLOCKED. See [handling-voyage evidence](../docs/candidate/handling-voyage.md) and [sanitized validation](evidence/kan-15-handling-voyage/validation.json).


## Latest current-capability checkpoint - 8 November 2026 (KAN-15 ACTION-42)

The handling completion checkpoint passed all four current role cases after strict invalid-time checks and unchanged-effects validation. Fresh fixture attempt 5 passed 661 native checks and owned cleanup. Current gate: 424 PASS / 46 BLOCKED; historical audit: 324 PASS / 178 BLOCKED; retirement: 76 BLOCKED. The overall gate exits 2 while those unrelated cases remain. Four prior fixture attempts and their dispositions are summarized in sanitized evidence at notes/evidence/kan-15-handling-completion/validation.json. Independent publication review is pending.


## KAN-15 BG-05 notification workers  8 November 2026

The disposable WildFly candidate fixture passed 723 checks, including protected consumer views for all four human actors and producer endpoint denials for anonymous, Reader, and Operator. A deliberately invalid handling-registration message received exactly three deliveries, was dead-lettered to the rejection queue, then acknowledged after one identifier-free `notification-worker` audit. Application tables were unchanged; empty queue and log hygiene checks passed. Candidate-runtime evidence is `notes/evidence/kan-15-bg05-gate/candidate-runtime.json`; design and limitations are in `docs/candidate/notification-worker-boundary.md`. Arbitrary external JMS/JNDI producer authorization remains unverified, so BG-05 machine capability remains blocked. Delivered and misdirected consumer bindings/startup are verified but their nonempty event cycles were not exercised in this isolated run. Shared services were preserved, and the owned fixture container and generated credentials were removed. Independent review and fresh full current-capability gate are pending.


## KAN-15 BG-05 full gate and recovery  9 November 2026

Jira KAN-15 remains In Progress. A fresh full current-capability run after the WSL/Docker restart passed 723 native and 841 browser checks. Owned app/browser containers, private network, and generated credential cleanup all passed; Jenkins remained running. The untouched full-run gate is 438 PASS / 32 BLOCKED; all 76 retirement cases remain BLOCKED (gate exit 2 is expected). Offline replay of six retained handling-event/voyage/completion Operator/Administrator browser proofs corrects an unrelated notification audit expectation, yielding 444 PASS / 26 BLOCKED. This replay did not rerun the runtime and does not change the original fingerprint. All four BG-05 human actor cases pass; BG-05-MACHINE remains blocked because external JMS/JNDI producer authorization was not exercised. The 438/32 total is the aggregate fresh report, not a BG-05-only delta from the older 424/46 checkpoint; subsequent BG-02/03/04 and browser-backed capability work is also represented. See `notes/evidence/kan-15-bg05-gate/replacement-gate-replay.json`.

The combined browser run logged one delivered and three misdirected notification audit events under `notification-worker`, with no MDB delivery authorization failures; the rejected-registration flow logged one event. The native BG-05 evidence records the exact rejection disposition and its counters. A reviewed harness refinement now compares every queue counter and business invocation delta against the explicit expected changes. An offline replay of the saved same-fixture before/after receipts passed, and negative mutations to an unrelated DLQ counter and unrelated business invocation were both rejected. This harness-only refinement did not change runtime code. Security unit tests: 88 PASS; focused comparator replay tests: 3 PASS.

Evidence: `notes/evidence/kan-15-bg05-gate/current-capability-gate.json`, `full-runtime-browser.json`, `candidate-runtime.json`, `notification-audit-lines.log`, and `rejection-delta-replay.json`. Independent review found no authorization defect and requested the wording/counter precision corrections; a final review of the corrected comparator and evidence remains pending. External producer authorization remains the next blocker.

The earlier WSL/Docker restart interrupted one full gate attempt and left only task-owned exited containers, an internal private network, and three mode-600 generated fixture credentials. The stale owned resources were identified and removed; the successful fresh run above confirms cleanup. Jenkins was not removed or restarted. The separate baseline-agent container is currently exited with code 127 after the restart and was not needed by this KAN-15 fixture.


## KAN-22 PostgreSQL/Flyway checkpoint (2026-11-09)

The pinned Java 25 candidate container build passed 35 tests (0 failures/errors). Fresh install applied Flyway V1, V2, and V3 on PostgreSQL 18.6 / Flyway 13.12.1. Runtime app insert succeeded; app DDL, Flyway history updates, and migration-state updates were denied. DATE equality and shared sequence generation passed.

Upgrade flow applied V1 alone, loaded synthetic rows across all six runtime tables plus legacy sequence state (high-water 8000), then applied V2 and V3. All rows remained present, DATE values were preserved, and the next shared ID was 8001. Detailed receipts and migration checksums: evidence/kan-22-postgresql/migration-contracts.json. Workflow: ../docs/database/postgresql-flyway-lab.md.

All disposable KAN-22 containers, networks, volumes, and generated secret files were removed; only the retained Jenkins container remains. WSL command rule: use a valid Windows working directory for the command runner and pass the Linux checkout using wsl.exe --distribution Ubuntu-24.04 --cd /home/yasinrdp/projects/ai-modernization --exec.

Independent review approved the corrected ACL and upgrade workflow. No production or retained-data import was tested. Candidate application deployment with the default persistence descriptor, PostgreSQL datasource and a disposable database is verified separately under KAN-18; see [runtime evidence](evidence/kan-18-postgresql-runtime/runtime.json).


## KAN-28 PostgreSQL recovery rehearsal (2026-11-09)

A disposable PostgreSQL 18.6 / Flyway 13.12.1 rehearsal passed. The V1 custom archive restored marker id 4501 and history version 1 in a separate rollback database while the active database stayed at version 3. After `restore-permissions.sql` repaired schema ownership and ACLs, `schema_migrator` applied V2, V3, and a temporary V4 probe. `cargo_app` inserted an explicit synthetic row. The V3 archive restored marker id 4501 at version 3; the repaired app role read it and Flyway applied the V4 probe. Both database states remained after a PostgreSQL container restart.

The tested restore repair is checked in at `infrastructure/database/restore/restore-permissions.sql`; exact procedure and evidence are in [the recovery guide](../docs/database/postgresql-backup-restore-rollback.md) and [rehearsal evidence](evidence/kan-28-recovery/rehearsal.json).

The disposable `kan28recovery` containers, named volume, private network, temporary credentials, and archive files were removed. Only the retained Jenkins container remains. This was single-host/single-version synthetic-data testing. It did not cover off-host or encrypted backups, scheduled automation, point-in-time recovery, cross-version restore, production-sized data, or compatibility with an actual older WildFly binary. Independent review approved the restore procedure, ownership/ACL repair, migration continuation and app-access evidence.


## Candidate Jenkins SCM checkpoint — 9 November 2026 (KAN-29)

Jenkins candidate build 3 passed from SCM at revision 92ebf5e169d775acd8756fe6854d0eab68972a2f. Toolchain: Java 25.0.5, Maven 3.10.0, Python 3.14.4 and Git 2.53.0. Eight setup tests, 68 checkout-safe security-contract tests, 11 runtime-harness tests and 35 Maven domain tests passed with zero failures/errors; six Surefire reports and the WAR/JAR/revision file were archived and fingerprinted. Polling H/15 * * * * is present in the candidate job config. The historical baseline was unchanged. The installed Declarative linter endpoint returned 403 to anonymous access, so its separate preflight remains unverified. The candidate identity was rotated to ai-modernization-candidate-secure, reconnected over WebSocket, and passed post-rotation Jenkins build 5 at fff69afad47a6ead3df49db1b834a1d78c76ceee. Build 4 was cancelled while queued on the offline pre-rotation node and has no test result. Polling remains H/15 * * * *. Independent review approved both the rotation changes and the new build evidence. Evidence: [KAN-29 summary](evidence/kan-29-jenkins-candidate/summary.json).


## KAN-18 PostgreSQL/WildFly runtime checkpoint - 10 November 2026

A bounded disposable run passed with the default candidate persistence descriptor. It built the Java 25 candidate image, deployed WildFly 42 with the pinned PostgreSQL JDBC 42.7.14 driver and PostgreSQL 18.6, and applied Flyway 13.12.1 V1/V2/V3 to a fresh database. The migration role authenticated; `cargo_app` DML succeeded and persistent schema DDL, temporary-table DDL, Flyway history updates and migration-state updates were denied.

The localhost endpoint at `127.0.0.1:8082` returned HTTP 401 anonymously. Reader, Operator and Administrator logins and protected REST reads passed; each retained the same database content snapshot. A synthetic marker row remained unchanged after application startup and restart, confirming no startup ORM DDL/seeding and restart persistence. The app uses a separate host-access Docker bridge for this local fixture; PostgreSQL remains only on the internal database network with no host-published port. The bridge gives the disposable app outbound network access.

Automated cleanup removed all fixture containers, networks, volumes, the unique candidate image and generated secrets. Evidence, versions, checks and file hashes are in [the KAN-18 runtime receipt](evidence/kan-18-postgresql-runtime/runtime.json). Independent post-run review approved the implementation and evidence. This is fresh synthetic-database evidence only; it does not cover retained legacy data import, production migration, a full data-upgrade rehearsal, or deployment outside this disposable local lab. KAN-15 remains In Progress; this runtime receipt alone does not close its broader acceptance gate.
