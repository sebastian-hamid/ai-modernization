# KAN-15 route-assignment action matrix

Scope: ACTION-17 and ACTION-19, sixteen active/logout/expiry cases. They map the historical itinerary-selection callbacks to the current native Faces route form. ACTION-17 opens admin/route.xhtml; ACTION-19 first exercises the protected admin/selectItinerary.xhtml GET alias and its fixed local redirect, then uses the current route form. The old callback implementation and retired alias POST are not claimed to execute.

## Exact chosen itinerary and independent effects

The driver loads real permitted form fields, CSRF and ViewState. It parses actual five-column candidate table body rows (voyage, from, to, departure and arrival), decodes entities and verifies the selected index is offered by the real select control. It never guesses a route payload or uses a different API response as the chosen itinerary.

Each permitted role uses its own fresh booking-control cargo, whose destination was changed to USNYC. Initial assignment requires NOT_ROUTED before submission. Replacement requires an existing ROUTED itinerary and selects a genuinely different displayed candidate. The specific actual POST must return a fixed local details redirect preserving the cargo ID. A separate Reader must see exactly the selected voyage/location/time rows in the persisted itinerary, unchanged origin/destination/deadline/transport/location and identical unrelated cargos. SQL must change and assignCargoToRoute must increase by exactly one; queues must remain unchanged because assignment does not publish JMS.

Anonymous and Reader entry requests must deny before cargo data loads. Their subsequent valid-form POST attempts each have separate settled before/after direct SQL, cumulative Artemis and EJB/MDB audit observations; all must remain identical. Anonymous 303 must target the configured local login; Reader 403 must disclose no cargo.

For each original entry, Operator and Administrator save their own real forms before native logout or at least 75 seconds of HTTP inactivity. Identity 401 is verified by the existing lifecycle driver. The saved form/cookie POST must redirect to local login, disclose no protected data and preserve all observer channels. The same route business endpoint is deliberately traced to two distinct original entry cases; it is not represented as execution of retired Faces code.

## Fail-closed binding and tests

Canonical callback/page/POST/write definitions and their original entry path are matched exactly. Real-form/source-entry proof, exact cargo query and pre-revocation ownership are required. Positive observations require concrete redirect status, SQL/audit/no-JMS evidence, exact selected/persisted itinerary equality, Reader deadline and unchanged unrelated cargo proof.

Focused tests reject missing/wrong candidate tables, unoffered/negative/out-of-range selections, malformed five-column rows, wrong form fields, missing SQL or audit delta, multiple invocations, JMS, changed cargo/state, wrong entry/target and incomplete session/positive proof. Previously verified booking/destination and full browser scenarios run in the same fresh fixture.

    python3 tests/security/run_candidate_contracts.py --live-subset --output .work/kan15-routing-actions/catalogue-results.json

## Acceptance boundaries

Fresh execution passed sixteen route cases and all prior bindings: 523 application checks, 431 Chromium checks and 77 tooling checks. The 35 reported domain cases retain one inherited empty TODO. Catalogue: 316 PASS / 186 BLOCKED, native exit 2. Task app/browser/network/private files were removed. Actual evidence is notes/evidence/kan-15-routing-actions, with final independent review recorded before publication. The full catalogue still exits 2 while unsupported definitions remain. Sample planner data is demonstration routing, not a verified carrier timetable optimizer. Isolated H2/Chromium and the inherited empty domain TODO remain disclosed. Task app/browser/network/private files must be removed and historical source/runtime/shared Jenkins preserved. No production deployment or role-policy change is included.
