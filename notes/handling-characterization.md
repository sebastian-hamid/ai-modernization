# Handling characterization baseline

The expanded suite preserves the pinned application source and dependency versions. New Java tests are copied only into an exported test checkout after the original WAR is packaged. Synced sources are read-only.

## Coverage

- 34 domain tests: 24 existing reports (including one empty Itinerary TODO), plus 10 factory tests for cargo/location/voyage lookup, required or prohibited voyages, and valid RECEIVE/LOAD events.
- Four existing booking integration tests.
- 15 HTTP characterization tests: full RECEIVE/LOAD/UNLOAD/CLAIM journey, five request validation cases, invalid event/date parsing, asynchronous lookup failures, invalid voyage combinations, lenient calendar parsing, and off-route loading after claim.
- 10 setup tooling checks, including two tests ensuring failed substeps and failed fixture setup produce failing JUnit reports.

## Observed legacy behavior

| Input or workflow | Current behavior |
| --- | --- |
| Seeded route to Helsinki | Transport state and location follow each event; destination flag is true after final UNLOAD and false after CLAIM. |
| Missing or malformed field lengths | HTTP 400; monitor state unchanged. |
| Unknown event type or unparsable timestamp | HTTP 500. These are existing defects, retained as characterization expectations. |
| Unknown cargo/location/voyage | HTTP 204 queues the request, then background processing logs a lookup failure. Cargo produces UnknownCargoException; real JPA location/voyage lookups throw NoResultException rather than returning null. |
| LOAD without voyage; RECEIVE with voyage | HTTP 204, then background factory validation failure. |
| February 30 | Accepted by lenient legacy date parsing. |
| LOAD after CLAIM on an off-route voyage | Accepted; cargo becomes ONBOARD_CARRIER and misdirected. |

The ten factory tests use repository doubles to characterize the factory's null-return contract separately from real JPA lookup behavior. HTTP acceptance alone never proves successful processing: positive cases poll cargo state, and asynchronous negative cases require new matching server-log evidence plus unchanged monitor state for a bounded interval. This does not establish final retry/dead-letter disposition.

## Reproduction and isolation

Jenkins runs the full suite through Jenkinsfile and ci/baseline.py, publishing 53 application test cases plus running 10 tooling checks. One original reported test remains an empty TODO; the HTTP smoke checks are additional assertions outside that count.

For standalone HTTP checks, create a disposable, freshly seeded runtime on a separate localhost port. Do not use the shared demonstration container: these tests mutate ABC123 and JKL567. The existing smoke test uses DEF789.

    python3 tests/runtime/handling_workflow.py --base-url http://127.0.0.1:8082/cargo-tracker/ --container ai-modernization-handling-tests --report-dir .work/handling-characterization --allow-mutation

Wait for the REST endpoint to be ready first. The runner requires a local HTTP URL, explicit mutation permission, and either --container or --server-log. Event dates use separate days in 2017, after the 2016 seeded events, because the legacy persistence mapping stores completion dates with DATE precision.

The standalone run passed all 15 cases. Reports and observations are in evidence/handling-characterization/. The original application checkout and shared demo data were preserved.

A disposable runtime restart exposed a separate deployment/persisted-state failure. An experimental force-redeploy change did not resolve it and was reverted. Recreate the disposable container for a fresh fixture; restart recovery remains a runtime follow-up, outside these test changes.

## Jenkins verification

Build 4 completed SUCCESS with 53 published application cases, zero failures/errors/skips, and 10 passing tooling checks. Evidence: [summary](evidence/jenkins-build-4/summary.json), [console](evidence/jenkins-build-4/console.log), handling reports and captured source manifest in the same directory. The original empty TODO is still included in the count. The archived snapshot includes an experimental Docker startup change unused by the native CI runtime; that change was reverted. All executed CI/test inputs match the final working tree, and the next-build snapshot was refreshed.
