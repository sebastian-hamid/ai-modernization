# Legacy runtime baseline
Verified 23 October 2026, Europe/Bratislava.

## Running application
- Application: http://localhost:8081/cargo-tracker/
- Public tracking: http://localhost:8081/cargo-tracker/public/track.xhtml (try ABC123).
- Administration: http://localhost:8081/cargo-tracker/admin/dashboard.xhtml
- Mobile logger: http://localhost:8081/cargo-tracker/mobile.xhtml
- Jenkins remains http://localhost:8080/.
- Compose project: ai-modernization-legacy; service cargo-tracker; container ai-modernization-cargotracker.
- Status at verification: healthy. Application HTTP 200 from both Windows and Ubuntu.
- Only the application HTTP port is published, bound to 127.0.0.1. GlassFish admin port 4848 remains inside the container network.
- Server runs as UID/GID 1000 with the pinned Java 8/Maven image used for the baseline build.

## Runtime recovery and precise deviation
Oracle's full GlassFish 4.1 release ZIP was retrieved over HTTPS:
https://download.oracle.com/glassfish/4.1/release/glassfish-4.1.zip

Observed/pinned SHA-256:
    3edc5fc72b8be241a53eae83c22f274479d70e15bdfba7ba2302da5260f23e9d

This digest pins the downloaded file; no publisher signature or independently published checksum was verified.

The stock distribution failed deployment with:
    ClassNotFoundException: org.hibernate.validator.internal.cdi.interceptor.ValidationInterceptor

The official issue [HK2-277](https://github.com/javaee/hk2/issues/277) identifies this exact Cargo Tracker/GlassFish 4.1 failure and the correction: bean-validator.jar incorrectly exports two CDI packages that are actually provided by bean-validator-cdi.jar.

The separate runtime image removes only those two false exports from bean-validator.jar's manifest. The preparation script asserts that every other JAR entry, including all class files, is byte-for-byte unchanged. It does not disable bean validation. The original ZIP and extracted source distribution are preserved. Original and corrected JAR hashes, WAR hash, container base and built image ID are recorded in [runtime provenance](evidence/glassfish-runtime-provenance.json).

This is GlassFish 4.1 with a documented module-metadata correction, not an unmodified runtime. Application source, application dependency versions and the deployed WAR remain unchanged from the recovered build.

## Start or recreate
From /home/yasinrdp/projects/ai-modernization in Ubuntu:

    # Requires an existing successful recovered build and its evidence manifest.
    python3 infrastructure/prepare-legacy-runtime.py
    docker compose -p ai-modernization-legacy -f infrastructure/compose.legacy.yaml up -d --build
    docker compose -p ai-modernization-legacy -f infrastructure/compose.legacy.yaml ps
    docker compose -p ai-modernization-legacy -f infrastructure/compose.legacy.yaml logs -f

Wait for healthy status before opening the application or running tests. To stop this runtime:

    docker compose -p ai-modernization-legacy -f infrastructure/compose.legacy.yaml stop

The legacy Compose file is separate from Jenkins. No Docker socket is mounted into either application or test containers.

The application explicitly clears/reloads its sample records on deployment/startup. It uses embedded Derby under /tmp/cargo-tracker-database and application-scoped JMS destinations defined in web.xml; no separate database service was needed. Treat these as disposable demo data. The smoke check intentionally changes DEF789. Recreating/restarting the runtime restores sample records; do not use it to preserve entered business data.

Two stopped diagnostic containers preserve the initial stock failure and the manually verified runtime:
- ai-modernization-cargotracker-stock-failed
- ai-modernization-cargotracker-manual-verified
They do not publish active listeners while stopped.

## Tests and observed behavior
### Arquillian booking integration
Run:

    bash infrastructure/test-legacy-integration.sh

The script exports the pinned application commit into a fresh ignored directory. A separate POM enables tests; all other POM/source content is unchanged. A temporary Java 8/Maven test container shares the application's network namespace, allowing Arquillian's default localhost:4848 admin and localhost:8080 application endpoints to work without publishing admin access to Windows.

All four ordered BookingServiceTest methods passed:
1. Register new cargo.
2. Fetch route candidates.
3. Assign route.
4. Change destination.

Results: 4 tests, 0 failures, 0 errors, 0 skipped.
Evidence: [booking log](evidence/runtime-integration-20261023-074039.ChqH43/booking-integration.log). The same directory contains Surefire XML reports and the server log.

### HTTP workflow smoke checks
Read-only checks:

    python3 infrastructure/smoke-legacy-runtime.py

To also exercise asynchronous handling on a freshly seeded runtime:

    python3 infrastructure/smoke-legacy-runtime.py --exercise-handling

Verified:
- Landing, public tracking, administration dashboard and mobile logger return HTTP 200.
- A session-aware JSF tracking-form submission renders ABC123.
- Routing returns 3–5 candidate routes, with connected legs and the requested origin/destination. The actual routes and dates are random; no exact route output is asserted.
- A JSON RECEIVE report for DEF789 at CNHKG returns HTTP 204.
- Polling confirms JMS processing changes DEF789 from NOT_RECEIVED/Unknown to IN_PORT/CNHKG. An accepted HTTP response alone is not considered a pass.
- The resulting routing status was MISROUTED, recorded as observed baseline behavior rather than altered to make the check pass.

Evidence: [workflow inputs and results](evidence/runtime-smoke-20261023-074056.json).

## Known limits and source discrepancies
- The old README's /incident-logger/ URL is absent in this commit and returned HTTP 404. The landing page uses mobile.xhtml.
- Sample deadlines/voyages use 2016 dates, while the route simulator generates current/random dates. This affects routing status and prevents exact deterministic route comparisons without controlling time/randomness.
- HandlingEventServiceTest, CargoLifecycleScenarioTest and ExternalRoutingServiceTest have no JUnit @Test annotations or TestCase inheritance and contain unfinished/commented setup. They are not counted as passing or as runnable Arquillian suites.
- The earlier domain run reported 24 passing tests; ItineraryTest.testNextExpectedEvent is an empty TODO.
- Browser JavaScript, external Google Maps/CDN assets, live WebSocket updates and CSV bulk handling have not been verified. Current smoke checks use server-rendered HTTP forms and APIs.
- The archived server logs include expired bundled certificate diagnostics. TLS verification was not disabled.
- Interactive Jenkins password login remains a manual check. The isolated baseline agent/job now passes; see jenkins-baseline.md. The reviewed setup is versioned locally as baseline-v0.1.0 and has not been pushed.

## Next milestone
The isolated Jenkins baseline pipeline now passes; see [jenkins-baseline.md](jenkins-baseline.md). Next review/version the source and expand characterization tests around meaningful cargo workflows before modernization changes.
