# Test coverage and access review

27 October 2026. Scope: pinned Cargo Tracker application in the isolated local lab. Production source and shared demo were preserved. This is a source-informed functional/access review, not a penetration test or a claim of complete statement/branch coverage.

## Verdict

The previous 53-case baseline was useful but insufficient for the requested input and direct-access review. Added **81 entrypoint contract cases**: the total is now **134 application cases** (34 domain, four booking integration, 15 handling workflow, 81 entrypoint cases), plus 10 tooling checks. One original domain case is an empty TODO. Substeps are assertions within cases, not additional cases.

Core service workflows and all declared REST resource families now have successful or observed-failure checks. We cannot claim all happy paths: full browser booking/routing/change-destination/mobile flows, CSV batch processing and real-time message delivery still lack end-to-end coverage. No coverage percentage was measured.

## Coverage matrix

| Area | Verified coverage | Remaining gaps |
| --- | --- | --- |
| Booking service | Register cargo, find candidates, assign route, change destination through existing Arquillian tests | Invalid/unknown booking inputs, transaction rollback, browser wizard/cancel/back/resubmit |
| Cargo domain | Original cargo/itinerary/route/event/history tests; factory lookup and voyage rules | Empty next-expected-event TODO; systematic boundary/property cases |
| Handling lifecycle | RECEIVE, LOAD, UNLOAD and CLAIM along the seeded route; CUSTOMS on unrouted cargo, with eventual monitor state | Duplicate/replayed/out-of-order concurrent events, all alternate routes, bulk import |
| Handling validation | Required fields missing/null/empty/short; excessive lengths for constrained fields; optional voyage boundaries; lowercase/unknown events; invalid location syntax; malformed/empty/null/array/object JSON; unsupported content types | Huge/deep payloads, numeric coercion matrix, Unicode/control characters, trailing date text, request-size/rate limits |
| Async handling errors | Unknown cargo/location/voyage, prohibited or missing voyage; new failure logs and bounded unchanged state | Final retry/rejection/dead-letter disposition and recovery |
| Cargo monitor REST | Real seed IDs, schema/boolean fields, JSON content type, HEAD, unacceptable response format, unsupported methods | Per-user data isolation once identities exist; pagination/large data |
| Route REST | Two origin/destination pairs; candidate count, connected legs, nonempty voyages and chronological dates; missing/short/long parameters | Unknown/same endpoints, repeated parameters, ignored deadlines, deterministic random/clock tests |
| Direct pages | Public pages and admin dashboard/list/map/detail/route/change-destination URLs without cookies; real cargo detail content | Full browser rendering, actions and client-side scripts; more ID variants |
| Private/missing resources | WEB-INF, template and META-INF direct access denied with 404; nonexistent page/API and cargo subresource 404 | Encoded path variants, alternate dispatch paths and error-page content review |
| Anonymous access | New HTTP opener without cookies or Authorization for every request; anonymous read and state-changing write; cross-origin WebSocket handshake | Authenticated/expired/logout sessions and role matrix: application has no configured identity/role model |
| Browser origin behavior | No Access-Control-Allow-Origin grant on cargo read; unrelated Origin accepted for WebSocket upgrade | Full CORS preflight matrix, CSRF via browser/form flows, live WebSocket frames |

## Confirmed access findings

Source inspection found no web.xml login/security constraints, REST role annotations or endpoint authentication controls. Live checks confirmed:

1. **Anonymous cargo data exposure:** monitoring JSON and real cargo details can be read without a login.
2. **Anonymous operational pages:** dashboard, cargo lists, map, route selection and change-destination views are directly reachable. A page GET does not prove every form action works.
3. **Anonymous write:** a CUSTOMS report for DEF789 at FIHEL returns 204 and changes last known location to FIHEL/IN_PORT. The test verifies a different prior location; acceptance alone is insufficient evidence.
4. **Anonymous cross-origin WebSocket:** /tracking returns a valid 101 handshake for Origin https://untrusted.example. No external host is contacted. This proves handshake acceptance, not message leakage or delivery.

The baseline contract suite deliberately records these existing behaviors. **Its passing result is not an access-control pass.** On the fresh standalone fixture, `--require-access-control` returned exit 1 with 13 observed operational surfaces; the log and machine-readable summary are in [review evidence](evidence/coverage-review-2026-10-27/strict-gate-summary.json). This is a proposed requirement for operational surfaces to require authorization; exact public/private routes and roles must be agreed before implementing controls. Public tracking and the route simulator are not assumed private.

There is no application login flow against which to test valid, invalid, expired or cross-role credentials. A fabricated Authorization header would not establish role coverage. Jenkins authentication is separate and was not attacked or changed.

## Other observed defects and limits

- admin/track.xhtml returns 500: the view references a missing destinationCoordinates property.
- Direct eventLogger/eventLogger.xhtml outside its JSF flow returns 500 (inactive FlowScoped context). mobile.xhtml redirects into the flow; this review checks its redirect destination, not successful completion of the flow.
- Missing/unknown IDs on cargo detail, itinerary selection and destination-change pages return 500 rather than controlled not-found/validation responses.
- Invalid enum case and invalid UN/LOCODE syntax return 500; existing unparsable timestamps and lenient invalid calendar behavior remain covered by handling tests.
- An exploratory raw WebSocket disconnect left stale sessions that caused cargo-inspection transactions to fail in that disposable runtime. The repeatable test now performs a masked RFC 6455 close handshake, and the final verification used a fresh fixture. Abrupt disconnect resilience remains a defect to reproduce separately; the shared demo was untouched.

## Reproduction

The CUSTOMS event uses a fixed 2030 completion date, after both the 2016 seed and the existing smoke event dated 2026. This characterizes acceptance of future-dated events without changing the server clock.

The Jenkins pipeline executes the entrypoint suite after existing handling checks, using its own fresh native GlassFish runtime. Expected entrypoint report count: 81. Reports, HTTP observations and a distinct security_findings list are archived under ci-results/entrypoints/. Baseline Jenkins success means observed contracts matched, not that the access-control requirement passed.

For a separate freshly deployed local fixture (these checks mutate DEF789):

    python3 tests/runtime/entrypoint_contracts.py --base-url http://127.0.0.1:8084/cargo-tracker/ --report-dir .work/entrypoint-review --allow-mutation --require-access-control

Expected current outcome: 81 characterization cases pass, but the explicit access-control gate exits 1. Do not reuse the fixture after mutation or run against the shared demo. The runner requires a local HTTP endpoint and explicit mutation permission; it follows no HTTP redirects automatically and uses no browser/session credentials.

## Priority before modernization release

1. Agree which operational routes/data/actions require which roles; add an expected-denial suite and implement authentication/authorization in a separate change. Do not publish this demo as a protected application.
2. Automate real browser booking, routing, destination change, tracking and mobile flows; turn the discovered direct-page errors into controlled behavior.
3. Add negative booking integration tests, replace the empty domain TODO, and exercise replay/concurrency, CSV and final JMS failure handling.
4. Add error-output, CSRF/XSS/injection, payload/traffic bounds, data isolation and disconnect-resilience tests against agreed requirements. Current checks do not establish absence of those vulnerabilities.

These are known coverage gaps, not claims that every possible bad path is practical to enumerate. Functional baseline assertions should remain separate from desired hardened behavior during migration.

## Final CI evidence

[Jenkins build 6](http://localhost:8080/job/ai-modernization-baseline/6/) completed SUCCESS with 134 reported application cases and 10 tooling checks. All 81 new entrypoint cases passed; 13 anonymous operational surfaces remain confirmed. The [summary](evidence/coverage-review-2026-10-27/jenkins-build-6-summary.json), exact source manifest, console log and entrypoint reports are preserved. Executed input hashes match the final working tree. Build 5 detected the fixture-date error; that failure and correction are recorded separately. No application production source was changed.
