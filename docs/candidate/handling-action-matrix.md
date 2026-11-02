# KAN-15 handling-submission action matrix

Scope: eight ACTION-41 active/logout/expiry cases, mapping the historical mobile handling callback to the current Faces form at /cargo-tracker/mobile.xhtml. Native GET first exercises the protected eventLogger/eventLogger.xhtml alias and fixed local mobile target. This does not claim the old callback or retired alias POST executes.

## Native form and asynchronous proof

The driver requires real offered cargo/location options, all current form fields, CSRF and ViewState. It submits CUSTOMS for two distinct fresh, routed/unclaimed native-control cargos: Operator at USCHI and Administrator at DEHAM. Completion times are valid and distinct; voyage is empty for this non-load event. The form must return HTTP 200 with the actual accepted-for-processing message.

Acceptance alone is insufficient. A separate Reader must observe the intended cargo become IN_PORT at the requested location, preserving ID/origin/destination/routing/deadline and every unrelated cargo. Direct SQL content must change. Each core queue (HandlingEventRegistrationAttemptQueue and CargoHandledQueue) must add and acknowledge exactly one message. Audited submitReport, registerHandlingEvent and the registration/inspection MDB onMessage calls must each increase by exactly one. All observations must settle with quiet queues before acceptance is recorded.

This verifies actual state propagation and the named channels, not exhaustive handling-event field/history persistence or every worker failure/retry scenario. Those broader gaps remain separate.

## Denied forms and native revocation

Anonymous and Reader entry requests must deny before loading cargo data. Each subsequent actual modern POST has its own settled SQL/JMS/audit snapshots, all unchanged; anonymous must redirect 303 to the configured login and Reader must return 403. The shared denial observer also inspects the specific target cargo ID for leakage.

Each permitted role saves its own offered form, CSRF token and cookie before actual logout or at least 75 seconds without HTTP traffic. Existing server identity 401 confirms revocation. Replay requests a later CUSTOMS event at FIHEL, different from the cargo's current location, and must redirect to login without cargo data or independent effects. Expired sessions are not refreshed to obtain new forms.

## Binding and tests

Only exact ACTION-41/PAGE-20/POST/write definitions and the legacy-entry-to-current-form mapping are bound. Positive proof requires real POST/form, source entry, exact cargo ID, accepted HTTP status/message and every specific asynchronous count/Reader flag. Generic success booleans, partial counters or bool-as-int counts cannot pass. Session proof additionally requires the original form was owned before revocation.

Focused tests reject missing/unoffered controls, incomplete SQL/JMS/audit/worker state, duplicate registration, wrong cargo/location/transport/destination, missing proof flags/counts, wrong source/path/method and modified canonical/session metadata. All prior action and browser cases run again in the same fresh fixture.

    python3 tests/security/run_candidate_contracts.py --live-subset --output .work/kan15-handling-action/catalogue-results.json

## Verification status and limits

Fresh execution passed all eight handling cases and all previous bindings: 565 application checks, 431 Chromium checks and 81 tooling checks. The 35 reported domain cases retain one inherited empty TODO. Catalogue: 324 PASS / 178 BLOCKED, native exit 2. All forty inventoried write-action/role/revoked-session cases now pass. App/browser/network/private files were removed. Evidence is notes/evidence/kan-15-handling-action, with final independent review recorded before publication. Full KAN-15 remains incomplete while unsupported read-only/internal contracts remain; native exit 2 is not a complete green security gate. The isolated H2/Chromium scope and one inherited empty domain TODO remain disclosed. Remove only task-owned resources/private files and preserve historical source/runtime/shared Jenkins. No production deployment or role/business-policy change is included.

The user approved the separately reviewed current-UI acceptance proposal on 2 November 2026. This increment records the approval but does not yet apply the versioned gate or reclassify any callback as retired. Replacement and negative-entry evidence are still required.
