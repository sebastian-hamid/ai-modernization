# Setup status
Verified 23 October 2026 (Europe/Bratislava). Checks ran on the actual WSL host, not the synced ChatGPT sources.

## Working
| Area | Evidence |
| --- | --- |
| WSL | Ubuntu-24.04 running as WSL version 2; Ubuntu 24.04.5 LTS; user yasinrdp. |
| Java | OpenJDK and javac 21.0.12.1. JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64. |
| Maven | Ubuntu Maven 3.8.7 at /usr/bin/mvn, home /usr/share/maven, uses Java 21. Verified fresh login and interactive shells. |
| Git | 2.43.0; main at 88e6479ea845745c362d567d55d1666acea05b49 before this work. |
| GitHub | gh authenticated as sebastian-hamid; origin https://github.com/sebastian-hamid/ai-modernization.git. Remote main matches local HEAD; repository is already PUBLIC. Visibility was not changed. Read access verified; no push performed. |
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
- Added baseline notes, logs and reproduction script. Initial setup made no commits or pushes. The reviewed setup is now versioned locally as baseline-v0.1.0; synced references remain untouched.

## Checks still requiring attention
1. Sign in to http://localhost:8080/ with your existing Jenkins account. No password was read or requested, and authenticated login was not tested.
2. Jenkins restart persistence is configured but was not exercised, to avoid interrupting the running controller. Plugin inventory and CI build-agent tools are unverified.
3. The reviewed setup is versioned locally as baseline-v0.1.0. Publishing it to GitHub and configuring SCM-triggered Jenkins execution remain separate steps.
4. Legacy packaging and domain tests now PASS after historical dependency recovery; see [legacy-baseline.md](legacy-baseline.md).
5. Runtime and booking integration now PASS: GlassFish 4.1 with the documented HK2-277 metadata correction, embedded Derby/JMS, four Arquillian booking tests, and HTTP tracking/routing/handling checks. See legacy-runtime.md. The isolated Jenkins baseline pipeline now passes; see jenkins-baseline.md.

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
The recovery script, settings, provenance hashes and reports are in infrastructure/ and notes/evidence/. Runtime milestone is now complete on host port 8081; see legacy-runtime.md. The isolated Jenkins baseline pipeline now passes; see jenkins-baseline.md. Next: broader behavior characterization; local setup versioning is complete.

## Runtime milestone completed
The application is healthy at http://localhost:8081/cargo-tracker/. Four booking integration tests and tracking/routing/asynchronous-handling HTTP checks passed against the Compose-managed runtime. Original GlassFish deployment failure, the module-metadata correction and remaining coverage gaps are documented in [legacy-runtime.md](legacy-runtime.md).

## Jenkins milestone completed
Build 1 of ai-modernization-baseline finished SUCCESS in 99.495 seconds. It published 28 reported tests (24 domain + four booking; one empty TODO), passed HTTP workflow checks and archived the WAR/provenance. A separate non-root Java 21/Java 8 agent runs all builds; controller executors are zero. Source mode remains a local snapshot. The reviewed setup is versioned locally as baseline-v0.1.0; publication and SCM integration remain pending. See [jenkins-baseline.md](jenkins-baseline.md).

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
