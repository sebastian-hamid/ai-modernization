# AI modernization lab: work completed

Recorded 27 October 2026. Brief factual record for later conversion into step-by-step AI agent instructions. This describes completed work, not a complete modernization procedure. Verification results below are from the recorded runs, most recently Jenkins build 4 on 26 October; services were not all reverified for this document.

## Purpose and boundaries

Established a reproducible legacy Java baseline before changing application behavior. The working repository is `/home/yasinrdp/projects/ai-modernization` in WSL Ubuntu. Preserved the original application checkout, existing Jenkins configuration and credentials, and shared demonstration data. Synced ChatGPT project `sources/` files remain read-only.

## Completed work, in sequence

1. **Verified and repaired the development environment.** Checked WSL2 Ubuntu, Java 21, JAVA_HOME, Maven, Git/GitHub access, Docker and local Jenkins. Installed Ubuntu Maven and made JAVA_HOME consistent across login and interactive shells. Kept Java 21 for modern tooling and isolated the legacy Java 8 toolchain.
2. **Organized the repository and evidence.** Added ignore rules, setup notes, reproduction scripts and provenance records. Reviewed and versioned the setup locally as `baseline-v0.1.0`. GitHub publication of these local changes and SCM-driven CI remain pending; the newer expanded test changes are still uncommitted.
3. **Recovered the legacy build.** Pinned Cargo Tracker to commit `57fc7b32d2597e43b5e0d454e707e0146de5258a`. Recovered historical Eclipse dependencies from their publisher and rebuilt the missing PrimeFaces theme/plugin from pinned official source. Packaged the unchanged application using a pinned Java 8/Maven image. Recorded origins and hashes; did not claim reconstructed artifacts were identical to historical published binaries.
4. **Established the original test baseline.** Enabled tests through a separate test POM because the original build skipped them. Verified 24 reported domain cases; identified one empty TODO and additional unfinished legacy test classes instead of treating them as meaningful coverage.
5. **Recovered the application runtime.** Recorded stock GlassFish 4.1 deployment failure and applied the documented HK2-277 manifest-only correction. Ran the application with embedded Derby/JMS on localhost port 8081. Verified four booking integration tests plus HTTP tracking, routing and asynchronous handling checks.
6. **Automated the baseline in Jenkins.** Preserved controller authentication and storage. Configured a separate non-root build agent, zero controller executors, no agent Docker socket and a local source snapshot with input hashes. Added pipeline stages for tooling checks, source/dependency recovery, packaging, domain tests and runtime checks; archived results and provenance.
7. **Reviewed and captured reusable lessons.** Checked setup scripts and safeguards, verified them in Jenkins, and created the `legacy-java-baseline` skill. Its reusable guidance is separate from repository-specific versions, paths and current status. See [skill notes](skills.md).
8. **Expanded behavior characterization.** Added 10 Java factory cases, 15 live handling workflow cases and two report-generation regression checks. Covered the complete handling journey, malformed inputs, asynchronous failures, lenient dates and off-route events. Added these checks to Jenkins without modifying application production source.

## Latest recorded outcome

Jenkins build 4 succeeded in 114.001 seconds: **53 application cases** (34 domain, four booking, 15 live workflow), with zero failures/errors/skips, plus **10 tooling checks**. One of the original domain cases is still an empty TODO. HTTP smoke assertions are additional checks outside this count.

The tests captured existing defects rather than fixing them: some invalid inputs return HTTP 500, some HTTP 204 requests fail during background processing, invalid calendar dates are accepted, and loading after claim is allowed. A disposable runtime restart also exposed an unresolved deployment/persisted-state failure; an attempted startup change was reverted. The shared demo was preserved.

## Lessons to carry into future agent instructions

- Inspect and preserve existing work before making changes; keep reference material read-only.
- Pin source/toolchains, isolate legacy execution, and retain dependency provenance.
- Separate unchanged application packaging from test-only overlays and runtime compatibility corrections.
- Confirm tests actually execute; distinguish meaningful assertions, empty tests and unfinished suites.
- Verify asynchronous state changes or fresh failure evidence; HTTP acceptance alone is insufficient. Bounded unchanged-state checks do not prove final JMS retry/dead-letter disposition.
- Use disposable seeded runtimes for mutating tests. Account for historical sample dates, date precision and random route output.
- Record failed experiments, exact corrections, evidence and remaining uncertainty. Verify a coherent change in CI before treating it as complete.
- Keep credentials out of instructions and evidence; keep project-specific facts separate from general agent guidance.

## Work still ahead

Define the project objective and acceptance measures; document the current architecture and risks; choose the target architecture and migration sequence; then modernize incrementally and compare against the baseline. Deployment/rollback, security/performance validation and measurement of AI assistance still need to be planned. The legacy baseline is established; the application itself has not yet been modernized.

Near-term follow-ups include reviewing/committing the expanded tests, Jenkins interactive login verification, GitHub publication and SCM integration, disposable runtime restart recovery, and prioritizing remaining browser/CSV/randomness/JMS coverage.

## Supporting records

- [Setup status](setup-status.md)
- [Legacy build recovery](legacy-baseline.md)
- [Runtime recovery](legacy-runtime.md)
- [Jenkins setup](jenkins-baseline.md)
- [Expanded characterization and limitations](handling-characterization.md)
- [Latest Jenkins result](evidence/jenkins-build-4/summary.json)

## Subsequent coverage review (27 October 2026)
Added 81 entrypoint contracts and verified Jenkins build 6 (134 application cases plus 10 tooling checks). Separately confirmed that the access-control requirement fails: anonymous operational reads/writes and cross-origin WebSocket handshakes are allowed. Documented remaining browser, identity/role, malformed-input, batch, concurrency and resilience gaps in [test-coverage-review.md](test-coverage-review.md). Application production source remains unchanged.

## Baseline documentation (28 October 2026)
Created source/evidence-checked functional, architecture and technical documentation under [docs/baseline](../docs/baseline/README.md), with commit-specific source references and a SHA-256 verification manifest. Clarified destructive startup initialization, two-minute batch scheduling, one-second attempt TTL and unverified rejection/dead-letter behavior. No application changes, service restarts or new runtime tests were performed; gaps remain explicitly labeled.

## 1 November 2026 — KAN-14 desired access tests

Defined 502 policy-derived actor/surface/session cases, with fail-closed candidate assertions. Sixteen oracle unit checks pass; these use artificial observations and are not application coverage. A fresh disposable legacy run reports two public-page successes and eight desired-security failures, including anonymous state mutation. Candidate gate explicitly reports all 502 BLOCKED (exit 2) pending real login/session/browser and independent effect observers in KAN-15. Shared services and original sources preserved. Independent review found two oracle false-pass paths; corrected with regression tests. Ticket remains In Review: actual denied-write queue/persistence absence verification awaits KAN-15 candidate security and independent observers. Local files only.

## 1 November 2026 — KAN-15 local identity/session foundation (in progress)

- Implemented reusable container-login, session CSRF/logout, explicit HTTP path roles and CDI method roles under candidate/security. Kept integration test WAR under tests/security-runtime separate from Cargo Tracker.
- Fresh pinned WildFly/Java25 fixture passes 49 runtime checks: actual local accounts/roles, session ID rotation, CSRF, direct service-role denial, logout replay and real server idle expiry. Three cleanup regressions pass (partial secret initialization, Docker log failure and container removal failure). Runtime/private realm files removed; historical source/demo/Jenkins preserved.
- This does not implement full KAN-15 or unblock KAN-14: actual Cargo Tracker candidate bootstrap (overlaps KAN-18), all callbacks/EJB/machine boundaries, WebSocket revocation and real database/queue/business-audit observers remain required. KAN-15 stays In Progress. See candidate/security/README.md; independent review/recheck complete with no remaining material foundation findings after cleanup correction. No commit/push. Human effort/review time/cost unavailable; no savings claim.

## 1 November 2026 — KAN-18 real candidate bootstrap / KAN-15 integration

- Exported 218 original source/test/resource/license files from pinned legacy commit into candidate/cargotracker, retaining original hashes and license. Added the existing ten-case factory characterization test. Migrated Jakarta APIs/build, current PrimeFaces adapters and standard REST/JMS/JPA declarations; historical source remains clean.
- Integrated reviewed local login/session/HTTP roles and EJB API/worker roles for real monitoring/handling only. Other operational routes deny by default pending UI/action/routing/WebSocket integration. First real runtime exposed failed MDB delivery authorization; preserved failure, corrected narrow internal delivery permission and retained worker authority.
- Final fresh disposable run: 34 domain tests (one inherited empty TODO), 35 runtime PASS and three cleanup regressions PASS. Actual Operator/Administrator JMS-driven persisted cargo changes verified; no independent denied-write DB/queue/audit absence claimed. Runtime/private files removed, historical demo HTTP200 and Jenkins preserved.
- Separate reviewer /root/review_kan18_bootstrap inspected source/provenance/limited security and independently ran cleanup regressions; fixed its non-material stale-context concern with fresh build directories. Final independent recheck verified218 original and237 current hashes,35 runtime results and3 independently rerun cleanup tests; no remaining material findings for this limited bootstrap. Both KAN-18/KAN-15 remain In Progress; KAN-14 still502 BLOCKED. See candidate/cargotracker/README.md and notes/evidence/kan-18-candidate. Local only, no commit/push. Human effort/review time/cost unavailable; no savings claim.

## 1 November 2026 — KAN-19 real browser workflow increment

- Implemented real Faces/PrimeFaces cargo list/details/booking/destination pages over existing business services, with Reader reads and Operator/Administrator mutations. Added HTTP+facade/EJB roles, session CSRF and exact static-resource/library policy. Routing/tracking/legacy mobile logger remain disabled; no full KAN-19 acceptance claimed.
- Browser testing exposed lazy DTO collection access, templated metadata placement and shared empty itinerary persistence ownership. Corrected transaction boundary, metadata client facet and per-cargo empty itinerary. Independent reviewer found an assigned-empty route fixture conflict; corrected to valid nonempty fixtures without changing three status assertions and added a distinct-empty NOT_ROUTED regression. Preserved sanitized failures.
- Final fresh run:30 Chromium assertions PASS,35 actual application runtime checks PASS,35 domain cases PASS (one inherited empty TODO),six mocked cleanup regressions PASS. Operator and Administrator create real cargos/change destinations and separate Reader sessions see persistence. Tests cover Reader links/forged POSTs, CSRF, invalid calendar/same-location inputs, controlled invalid IDs, resource bypass and tested mobile details viewport.
- Task-owned app/browser/private network removed; memory-only browser credentials and private realm files removed. Historical app HTTP200, original source clean and Jenkins preserved. Full KAN-14 independent DB/queue/audit absence still unverified;502 candidate definitions remain BLOCKED. KAN-15/KAN-18/KAN-19 stay In Progress.
- Independent review/recheck complete: all250 hashes match,30 browser/35 application/35 domain results inspected and six cleanup regressions independently rerun; no remaining material findings for this bounded increment. Local uncommitted/unpushed. Human effort/review time/cost unavailable; no savings claim. See docs/candidate/browser-workflows.md and notes/evidence/kan-19-browser.

## 1 November 2026 — KAN-19 routing and scoped internal identity

- Integrated actual sample route request/selection/assignment/rerouting in Faces with server-held choices, O/A HTTP/facade/EJB permissions, session CSRF and current-spec validation for committed stale candidates. Kept legacy demonstration planner explicit; no real timetable optimization claim.
- Preserved internal HTTP with a separate native WildFly RoutingService account, private per-run client credentials, fixed loopback endpoint, redirects disabled/timeouts/client close. Machine Basic authentication exists only at graph API; credentials are never forwarded from humans or provided to browser fixtures. Per-request identity/session cleanup and third-secret failure regression added.
- Actual assignment exposed Hibernate orphan-delete collection replacement failure; changed aggregate-owned legs in place with defensive input copy, preserving existing domain assertions. Retained first failure. Reviewer requested stronger exact sequence and empty-candidate checks; implemented both and real rerouting per human mutation role.
- Final fresh run:63 Chromium assertions PASS,47 application checks PASS,35 domain cases PASS (one inherited empty TODO),seven mocked cleanup tests PASS. Exact selected/replacement voyages/locations/times and separate Reader readback, stale/invalid/forged/CSRF denials, role credentials and empty candidate case verified. No independent denied-write DB/queue/audit absence claim.
- App/browser/private network and three private realm/client files removed; historical app HTTP200, source clean and Jenkins preserved. KAN-15/KAN-18/KAN-19 remain In Progress; KAN-14 still502 BLOCKED. Independent review approved publication with no remaining material findings:253 hashes verified,63/47/35 records inspected,seven cleanup tests independently rerun; coverage/Javadoc notes resolved. Publication proceeds under standing authorization. Human effort/review time/cost unavailable; no savings claim.

## 1 November 2026 — KAN-17 endpoint session security

Implemented authenticated/origin-allowlisted session-bound sockets, logout and HTTP-idle closure, and safe send failure isolation. Actual89 browser/47 application/35 domain PASS (one inherited empty TODO). Independent reviewer /root/review_kan17_socket approved code/docs/evidence, verified255 hashes; no remaining material findings. Map UI remains disabled; malformed/abrupt variants source-review only. Task runtime/network/private files removed; original services preserved. Published under standing authorization; full candidate/KAN-14 acceptance remains open. Human effort/cost unavailable.

## 1 November 2026 — KAN-19 live tracking UI

Restored authenticated live cargo plot/table with local assets, real inspection updates, marker/detail links, connection state and DOM clearing on logout/idle expiry. Preserved original socket name fields with added explicit codes; generation/abort/time ordering guards prevent stale snapshot replacement. Final107 browser/47 application/35 domain PASS (one inherited empty TODO); seven mocked cleanup regressions PASS. Actual all-role UI updates/marker movement, delayed snapshot, post-revocation empty views and authorized post-expiry event verified. Historical services/source preserved; task resources removed. Independent review/recheck approved publication with no remaining material findings;261 hashes verified and seven mocked cleanup tests independently rerun. Unique final NewYork event confirms post-expiry delivery. KAN-19 mobile logger remains open; KAN-14 independent absence still unverified. No savings/cost/time claims.

## 1 November 2026 — KAN-19 responsive handling completion

Replaced obsolete mobile flow with direct responsive form preserving routed/unclaimed eligibility; O/A path+EJB roles and CSRF, known choices/LOAD-voyage/calendar checks, accurate asynchronous acceptance. Final126 browser/47 application/35 domain PASS (one inherited empty TODO). Distinct O/A CUSTOMS and LOAD persistence verified by Reader; direct/forged Reader and missingCSRF denied. Independent reviewer /root/review_kan19_mobile approved scopedUI publication, verified263 hashes and clean evidence; no material findings. Full platform/security/effect observers remain open; legacy aliases separate KAN-20. Task resources removed; historical services preserved. Standing authorization publication applied; no full CI or runtime redeploy for publication. Human effort/cost unavailable.

- **KAN-15 current gate checkpoint (2 November 2026):** Independently verified the corrected v2 scaffold (54 security unit tests), ran its first fresh native/browser integration, and recorded 308 current PASS / 162 BLOCKED plus 76 retirement BLOCKED. Historical audit remains 324/178. Missing booking/destination entry provenance fails closed; no retirement or full-acceptance claim. Disposable cleanup passed. Next: prove actual source-entry flows before changing evidence metadata.

- **KAN-15 source-entry proof (3 November 2026):** Added real booking source and selected-cargo destination link checks, role-specific denied GET/direct POST coverage, and pre-revocation entry receipts. Corrected an encoded Faces window-query guard after one cleaned-up failed run. Fresh current gate324PASS/146BLOCKED (16 prior gaps resolved); historical324/178 and76retirementBLOCKED preserved. Native565/browser431passed;32fixture+54securityunit tests passed. Next: implement the14pending current-equivalent behavior drivers.

- **KAN-15 current load behaviors (3 November 2026):** Implemented destination-form and cargo-details GET equivalents separately from historical callbacks. All four actors, independent selected-cargo values, distinct destination controls and24invalid-ID cases pass. A monitored hold after repeated field mismatch led to a bounded compiled-getter diagnosis and location-name-only whitespace normalization. Latest current332PASS/138BLOCKED; legacy324/178 and76retirementBLOCKED retained. Native603/browser431checks,36fixture+56securityunits passed. Next: remaining12current behaviors(48cases),11replacementgroups(44cases),46internal boundaries and conditional retirement verifiers.
