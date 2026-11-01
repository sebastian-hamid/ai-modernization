# KAN-13: minimal Java 25 / Jakarta EE 11 / WildFly spike

This is an isolated capability WAR, **not migrated Cargo Tracker**. It contains no original application code or production data. Prepared 1 November 2026.

## Result and identities

The recorded run passed 19 checks: Java 25 execution and class-file major version 69; non-root runtime; authenticated R/O/A reads; anonymous/bad-password denial; rendered Faces/CDI expression; Reader/anonymous write denial with unchanged row count; Operator and Administrator creation; actual JPA persistence, JMS consumer update and COMPLETED batch execution for both; exact authorized row count; 404 and unsupported-method handling. [Results](../../notes/evidence/kan-13-runtime/results.json) and [JUnit](../../notes/evidence/kan-13-runtime/TEST-kan13-runtime.xml).

- Standard WildFly 42.0.0.Final full configuration, not Preview. Base image: `quay.io/wildfly/wildfly@sha256:3fc71f6c4fe1075ac942dbb652799840ecd5424458def6039f829bf3221a8daf`.
- Build image: `maven@sha256:9d329e21adce7c0cc53f2fd21e73c127a247c73287b8503196136ec5cff52328`. Runtime JDK is copied from this pinned image to use Temurin 25.0.5+8; official WildFly base contained 25.0.4.1. This is an assembled test image, not an unchanged official WildFly image or a new vendor/TCK certification claim. Headless Linux capability checks pass; TLS/native/GUI and other workloads are not proven.
- Jakarta EE API 11.0.0 (provided), compiler plugin 3.16.0, WAR plugin 3.5.1; release bytecode 25. Compiler 4.x beta was not selected. Maven/tool output and artifact/source hashes are recorded in evidence; build plugins/API remain pinned rather than dynamically following latest at reproduction time.

## Reproduce from WSL

Prerequisites: Docker/WSL integration, Python 3, free local port 8085 and access to the pinned registries/Maven Central. Work in `/home/yasinrdp/projects/ai-modernization`:

    python3 spikes/kan13-runtime/run_spike.py

Optional `--port` selects a different unprivileged port. The harness refuses an existing `ai-modernization-kan13` container; it does not reuse or delete unrelated containers. It builds the pinned image, generates per-run local ApplicationRealm credentials in ignored `.work/kan13/secrets` with private permissions, mounts them read-only, publishes only `127.0.0.1:8085:8080`, checks observable effects and removes the exact task container/private realm files. No password or Authorization header is written to the report or image. Never print private realm content.

Image build inputs are under src/, pom.xml, Dockerfile and start.sh. Logs/cache/WAR remain local under `.work/kan13`; small sanitized summaries and assertions are versionable under notes/evidence/kan-13-runtime. The report contains no test passwords. The runtime image remains locally cached. Results reflect a successful disposable run, not an always-running service.

## Implementation and boundaries

- HTTP BASIC is used only to probe local-account/role capabilities over the isolated loopback fixture. There is no approved application form-login/session/logout implementation here; full CSRF, expiry, WebSocket and KAN-12 access-policy tests remain later work.
- Protected `/api/status` reports actual JVM version and row count. `/api/probe` POST permits Operator/Administrator at HTTP and EJB boundaries; Reader is denied. `/api/probe/{id}` and `/api/batch/{id}` report the record and actual batch status.
- JPA uses WildFly ExampleDS/H2 with drop-and-create strictly for this disposable capability fixture. It does not test PostgreSQL, Flyway, durable data, restart recovery or the legacy ORM mapping.
- Creation commits a record and JMS send before starting the batch. The MDB and batchlet update different columns using targeted database updates, avoiding concurrent flag lost updates. Polling requires both worker effects and batch status COMPLETED; HTTP acceptance alone does not pass.
- A Faces view evaluates a CDI bean, rather than merely returning a static page. PrimeFaces/mobile/theme compatibility and all Cargo Tracker workflows remain unverified.
- Internal ProbeService permits trusted in-process probe calls; no remote business endpoint/production service-security design is claimed. Broker/worker identities and audit propagation for Cargo Tracker are still KAN-15 design work.

## First-run finding

Initial local authentication/read/Faces checks passed, but the Reader POST check did not produce the expected 403. Server logs showed EJBAccessException from the method-role interceptor surfacing through the default REST exception mapper. Added an explicit method/path HTTP constraint for POST /api/probe, retaining EJB role checks. The corrected run returns 403 and leaves row count unchanged. [Initial failed result](../../notes/evidence/kan-13-runtime/first-run/results.json) is retained; the original harness did not capture that response status and its JUnit failure used a generic completion case. The harness now records response statuses and attaches failures to their actual check, with robust cleanup/reporting.

## Harness cleanup regression

A separate reviewer identified a non-material initialization edge case: realm files were written before the main cleanup guard. Initialization now runs inside try/finally. A fault-injection regression forces the second realm-file write to fail, with Docker mocked, and verifies the first private file is deleted and a failing JSON/JUnit result is written. Run it separately:

    python3 -m unittest discover -s spikes/kan13-runtime -p test_harness.py -v

The one harness regression check passes; a fresh disposable runtime rerun also passes all 19 capability checks after the hardening change. This is separate from the capability test count.

## Decision and remaining work

The minimal checks support continuing with Java 25.0.5/Jakarta EE 11/standard WildFly 42 as the candidate foundation. This is a compatibility-spike conclusion, not acceptance of the full migration or security remediation. WildFly recommends Java 25 but its published EE 11 compatibility claims cover Java 17/21; this spike does not change that distinction.

Next: implement desired access tests from KAN-12 (KAN-14), then actual candidate security/application migration work. Keep the historical GlassFish container, Java 8 build agent, existing Jenkins job and original source untouched.

References checked 1 November 2026: [WildFly 42 release](https://www.wildfly.org/news/2026/10/22/WildFly-42-is-released/), [Elytron application-realm/security configuration](https://docs.wildfly.org/42/WildFly_Elytron_Security.html), [Jakarta XML schemas](https://jakarta.ee/xml/ns/jakartaee/).
