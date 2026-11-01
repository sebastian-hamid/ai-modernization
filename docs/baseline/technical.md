# Legacy baseline: technical documentation

Prepared 28 October 2026 from pinned source, lab scripts and archived test evidence. No build, server restart, deployment or mutating workflow was performed to write these documents. [Verification and evidence](README.md) distinguish source declarations from recorded runtime results.

## Environment and repository

Work in WSL Ubuntu-24.04 at `/home/yasinrdp/projects/ai-modernization`. The Windows ChatGPT project mirror is reference material; synced `sources/` is read-only. Historical source is the ignored checkout `experiments/legacy-cargotracker`, pinned to `57fc7b32d2597e43b5e0d454e707e0146de5258a`. Do not edit it to modernize the application; create the planned versioned candidate separately.

| Area | Recorded baseline |
| --- | --- |
| Development host | WSL2 Ubuntu; Java 21/JAVA_HOME and Ubuntu Maven repaired and verified in setup work. |
| Historical application | Java EE 7 WAR, Java 7 compiler target, Java 8 execution, PrimeFaces 5.2, JUnit 4.12 and Arquillian. |
| Runtime | GlassFish 4.1 with manifest-only HK2-277 compatibility correction; embedded Derby/JMS. |
| Build recovery | Pinned Java 8/Maven image; publisher-hosted Eclipse artifacts; theme/plugin rebuilt from official pinned sources, with provenance and hashes. |
| Local HTTP | Demo `http://localhost:8081/cargo-tracker/`; Jenkins `http://localhost:8080/`. Loopback publication is configured; live availability was not rechecked here. |
| CI isolation | Java 21 remoting plus Java 8 build agent; no Docker socket; exact read-only source snapshot copied into build workspace. Native temporary GlassFish uses its own localhost:8080/4848. |

Source: [original POM](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/pom.xml). Lab authorities: [setup](../../notes/setup-status.md), [build recovery](../../notes/legacy-baseline.md), [runtime recovery/provenance](../../notes/legacy-runtime.md), [CI](../../notes/jenkins-baseline.md). Historical recorded versions are not claims that these are current supported releases.

## REST API reference

Base path: `/cargo-tracker/rest`. The baseline declares exactly these three REST resource families. Booking mutations are application/JSF service calls, not invented REST booking endpoints. Paths below describe the historical anonymous interfaces; the target must enforce the approved access policy.

| Method/path | Request | Response / behavior |
| --- | --- | --- |
| GET `/cargo` | Accept application/json | 200 JSON array of every cargo; no user filtering or pagination declared. HEAD is also verified with no body. |
| POST `/handling/reports` | Content-Type application/json; report object below | 204 after queue submission. Basic input validation can produce 400, unsupported media 415 and parse/domain construction errors 500. Asynchronous failure may occur after 204. |
| GET `/graph-traversal/shortest-path` | origin and destination: non-null strings of length 5; optional deadline query | 3–5 random candidate paths in verified requests; JSON or XML declared. Source takes deadline but does not use it; adapter later filters converted itineraries against the route specification. |

Sources: [REST configuration](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/application/util/RestConfiguration.java), [monitor](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/interfaces/booking/rest/CargoMonitoringService.java), [reports](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/interfaces/handling/rest/HandlingReportService.java), [graph](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/pathfinder/api/GraphTraversalService.java).

Cargo JSON fields: trackingId, routingStatus, misdirected (boolean), transportStatus, atDestination (boolean), origin and lastKnownLocation. Locations are codes; unknown location maps to the literal `Unknown`. Each graph candidate contains transitEdges with voyageNumber, fromUnLocode, toUnLocode, fromDate and toDate; exact random outputs are not fixed fixtures. No stable error-envelope schema is established.

### Handling report contract

| Field | Declared validation | Further behavior |
| --- | --- | --- |
| completionTime | Required, exactly 16 characters | Parsed using `yyyy-MM-dd HH:mm` with default SimpleDateFormat leniency; no timezone is supplied by the request. |
| trackingId | Required, minimum 4 characters; no maximum declared here | Must resolve to a known cargo during asynchronous registration. |
| eventType | Required, 4–7 characters | Case-sensitive enum RECEIVE/LOAD/UNLOAD/CUSTOMS/CLAIM; shape-valid unknown enum can return 500. |
| unLocode | Required, exactly 5 characters | Must satisfy UnLocode construction and resolve to a location. |
| voyageNumber | Optional/null permitted; if supplied, 4–5 characters | Required for LOAD/UNLOAD; prohibited for RECEIVE/CUSTOMS/CLAIM. Semantic rules are checked during registration. |

Illustrative LOAD body, **not a command to run against the shared demo**:

```json
{
  "completionTime": "2017-01-02 10:00",
  "trackingId": "ABC123",
  "eventType": "LOAD",
  "unLocode": "CNHKG",
  "voyageNumber": "0100S"
}
```

This example is valid only in an appropriate disposable fixture and does not guarantee a correct next event for arbitrary cargo state. [DTO constraints](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/interfaces/handling/rest/HandlingReport.java); [event factory](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/domain/model/handling/HandlingEventFactory.java).

## Pages and WebSocket

Page groups are landing/index, public tracking/about, admin dashboard/lists/detail/route/itinerary/change-destination/map/tracking, booking Faces flow, mobile entry and eventLogger flow. The complete source page list is in [verification.json](verification.json). Source existence does not establish a successful direct-link contract: flow pages require flow context, and some views are broken.

`/cargo-tracker/tracking` is the WebSocket endpoint. Source broadcasts trackingId, origin, destination, lastKnownLocation and transportStatus; location fields here use human-readable names, unlike monitor REST codes. It sends to registered sessions without per-user filtering and sets a five-minute socket idle timeout. Tests verified anonymous cross-origin upgrade and a valid handshake response; complete message/frame and browser-delivery tests remain open. [WebSocket implementation](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/interfaces/booking/socket/RealtimeCargoTrackingService.java).

## File import/batch contract (source-reviewed, not end-to-end verified)

`UploadDirectoryScanner.processFiles` uses `@Schedule(minute = "*/2", hour = "*")`: every two minutes, despite the source comment saying fifteen. It starts EventFilesProcessorJob with no supplied parameters. The job XML configures `/tmp/uploads`, `/tmp/archive`, `/tmp/failed`, a chunk size of 12 and skipping EventLineParseException. These are runtime-local paths, not a documented authenticated upload API.

Input rows are split on literal commas into exactly five values, in this order:

```text
completionTime,trackingId,voyageNumber,unLocode,eventType
2017-01-01 10:00,ABC123,,CNHKG,RECEIVE
```

The first line above describes columns; **do not include it as a file header**. No quoted-CSV/header handling or whitespace normalization is implemented by the simple splitter. Voyage may be empty in the third field. Date parsing is lenient. Reader collects files, uses byte-offset checkpoints and deletes a file at EOF; writer queues registration attempts and appends a six-field archive row including registration time. Failed parse lines are appended separately. The archive format is not an input round-trip format. File deletion/archive and JMS processing must not be assumed atomic or replay-safe.

Batch exception handling is narrower than a universal invalid-row policy: configured skipping applies to EventLineParseException, and constructor/runtime exceptions are not all wrapped into that type. The reader lists directory entries without an explicit file/extension filter. Skipped parse errors are written to failed output, whereas later asynchronous registration failure is a separate path. Header/quoted CSV, directories mixed with files, interruption, file cleanup, duplicate/replayed import and final failed-message disposition are still execution gaps.

Sources: [scanner](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/interfaces/handling/file/UploadDirectoryScanner.java), [reader](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/interfaces/handling/file/EventItemReader.java), [writer](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/interfaces/handling/file/EventItemWriter.java), [job XML](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/resources/META-INF/batch-jobs/EventFilesProcessorJob.xml).

## Configuration and data lifecycle

| Setting | Current declaration | Consequence |
| --- | --- | --- |
| GraphTraversalUrl | POM property rendered into web.xml; default local `/cargo-tracker/rest/graph-traversal/shortest-path` on port 8080 | Container-local address; protecting this route requires changing internal-client authentication. |
| CargoTrackerDatabase | web.xml application-scoped embedded Derby URL under configured databaseTempDir, default `/tmp` | No separate PostgreSQL in the baseline. |
| CargoTrackerUnit | JTA application data source; schema-generation action `create`; EclipseLink logging FINEST | Demo-oriented lifecycle/verbose logs, not controlled schema migrations. |
| SampleDataGenerator | Startup singleton calls unLoadAll then repopulates | Existing entity data is deleted during startup/deployment initialization. |
| GlassFish compatibility | Two false CDI exports removed from validator JAR manifest; classes otherwise preserved | Separate corrected runtime; stock failure/provenance retained. |
| Security | web.xml has no login/security constraints; source review and HTTP tests confirm open operational surfaces | Approved local accounts and roles are target work, not existing protection. |

See [architecture](architecture.md) for relationships, queues and the 1000-ms attempt TTL. Current schema is ORM-generated; no complete physical DDL export, FK/index catalog or Derby-to-PostgreSQL mapping has yet been verified. These are required before database migration.

## Reproduce and verify

Run commands from the WSL repository root. The documentation review itself did not execute these mutating/build commands.

```bash
# Fresh shell: read-only tool resolution checks.
printenv JAVA_HOME
java -version
mvn -version
git -C experiments/legacy-cargotracker rev-parse HEAD

# Recovery builds an isolated pinned export: original 24 reported domain cases.
bash infrastructure/recover-legacy-baseline.sh

# Read-only application smoke (requires an already-running baseline runtime).
python3 infrastructure/smoke-legacy-runtime.py

# Setup/report regression tests; no live application mutation.
python3 -m unittest discover -s tests -v
```

The recovery script's original 24 cases are not the expanded 134-case CI suite. The [Jenkinsfile](../../Jenkinsfile) and [ci/baseline.py](../../ci/baseline.py) orchestrate recovery/package, 34 domain, four booking, 15 handling and 81 entrypoint cases. It archives reports even on failures. One original domain method is still empty; 10 tooling checks are separate. Tests assert actual state or fresh error evidence for asynchronous behavior.

After changing pipeline inputs, refresh the local snapshot while idle:

```bash
python3 ci/update-local-snapshot.py
```

Then use Build Now on the existing baseline job. Jenkinsfile definition changes also require updating the installed inline pipeline; a snapshot refresh alone does not update it. See the [Jenkins runbook](../../notes/jenkins-baseline.md) for controller/agent registration and secret handling. No credentials are documented here.

Runtime build/start instructions are in [legacy-runtime.md](../../notes/legacy-runtime.md). **Do not restart or recreate the shared demo to preserve entered data:** startup deliberately clears sample records, and disposable restart/deployment recovery has a separate known failure. An earlier runtime note's broad statement that restart restores samples does not establish that every restart succeeds. Use a newly created, separately named disposable fixture for mutating tests and investigate recovery independently. Do not delete Jenkins volumes or use `down -v`.

Standalone handling/entrypoint suites require a local base URL, explicit `--allow-mutation` and fresh fixture state. Existing smoke mutates DEF789, handling suite ABC123/JKL567, and entrypoint suite uses a later CUSTOMS event for DEF789. Run the pipeline's documented order or prepare the required independent fixture; do not replay these on the shared demo.

## Troubleshooting and remaining verification

| Symptom | Recorded cause / next investigation |
| --- | --- |
| Dependency resolution failure | Historical repositories/artifacts; use pinned recovery/settings and provenance rather than disabling TLS or substituting silently. |
| Stock deployment ValidationInterceptor error | Known HK2-277 false manifest exports; use the narrowly corrected runtime preparation. |
| 204 with no cargo update | Check event completion ordering/DATE precision, fresh server processing errors, queue TTL and retries. Do not infer success from acceptance. |
| admin/track 500 | Missing destinationCoordinates property referenced by the view. |
| Direct eventLogger 500 | FlowScoped context absent when bypassing flow entry. |
| Missing/unknown cargo direct-link 500 | Unhandled lookup/validation failure. |
| Aborted WebSocket followed by inspection failures | Exploratory disposable runtime showed stale-session send errors affecting transactions; resilience remains to be reproduced and fixed separately. |
| Restart/deployment failure | Preserve logs; inspect registered deployment, initializer and local database state. Force-redeploy experiment was reverted and is not a verified remedy. |

[Coverage review](../../notes/test-coverage-review.md) is authoritative for tested examples and limits. Backup/restore, rollback, durable candidate restarts, Flyway schema management, authenticated/expired/role-specific access and measured performance are approved future acceptance requirements, not completed baseline features.
