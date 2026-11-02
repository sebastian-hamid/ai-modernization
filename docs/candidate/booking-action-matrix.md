# KAN-15 booking action matrix

Scope: ACTION-29, the historical booking registration callback, mapped to the current Faces booking form at /cargo-tracker/admin/book.xhtml. The original flow callback is not claimed to execute. Current native HTTP form submissions exercise its modern booking behavior. This increment defines eight cases: four active actors plus Operator/Administrator logout and idle-expiry replay.

## Transport metadata

The authoritative source inventory generator now emits POST for the five domain-mutation callback definitions (ACTION-09, ACTION-17, ACTION-19, ACTION-29 and ACTION-41). Regenerating the desired catalogue changes only the method field in 40 definitions; all 502 IDs, roles, expected outcomes and write/session requirements remain unchanged. Other mutation definitions remain unsupported until their own specific drivers and evidence exist. Navigation descriptors keep their existing default GET.

A regression regenerates the complete inventory into a temporary output using the pinned read-only historical source and requires exact equality with the checked inventory. Regeneration does not edit the historical checkout.

## Native form driver and effects

The existing disposable fixture renders a real permitted booking form and submits actual application/x-www-form-urlencoded POST with real ViewState and CSRF fields. No new observer endpoint, browser coordinator, production business logic or role policy is introduced.

Anonymous and Reader replay the permitted form as forbidden callers. Each individual POST has its own settled before/after direct SQL content hashes, cumulative Artemis queue counters and EJB/MDB invocation snapshots. Anonymous must receive 303 to the configured local login; Reader must receive 403; both responses are inspected for cargo leakage. Database, queue and audit snapshots must remain unchanged.

Operator and Administrator each render their own form and book one new CNHKG-to-FIHEL cargo with deadline 2030-12-31. The actual POST must return a fixed local 302/303 details redirect with exactly one valid new tracking ID. Actor details return 200; a separately authenticated Reader verifies the unique new REST cargo, origin/destination, NOT_ROUTED/NOT_RECEIVED state and persisted deadline through the details view. Independent observations must show changed SQL content and exactly one additional bookNewCargo invocation. Booking does not send JMS: unchanged queues are explicitly required, rather than inventing a worker event.

Each logout/expiry replay uses the same role's form and token captured while its own native session was authenticated. Real logout or at least 75 seconds without HTTP activity revokes that session; the existing lifecycle driver verifies its identity endpoint returns401. The saved cookie/form POST must return the configured login redirect with no payload and unchanged independent snapshots. Expired sessions are not refreshed to obtain a new form.

## Fail-closed binding

Only exact canonical ACTION-29 callback/page/POST/write definitions are bound. The adapter also requires the modern POST path, real-form evidence and pre-revocation ownership for session cases. Positive observations need concrete redirect status, generated ID, SQL change, booking invocation delta, zero-JMS expectation, independent Reader cargo and deadline evidence. Generic success booleans alone cannot promote a booking case.

The complete security gate still exits 2 while unsupported contracts remain. Do not count historical reports or a rendered GET as executed write evidence. Existing browser workflows and all previously bound cases run with the fresh native fixture.

Run from WSL:

    python3 tests/security/run_candidate_contracts.py --live-subset --output .work/kan15-booking-action/catalogue-results.json

## Verification status

Fresh runtime passed all eight booking cases: 411 application checks, 431 Chromium checks and 68 tooling checks. The 35 reported domain cases retain one inherited empty TODO. Catalogue: 292 PASS / 210 BLOCKED, native exit 2; full KAN-15 remains incomplete. Task app/browser/network/private files were removed; historical HTTP 200, clean historical source and shared services preserved. Final separate review is recorded before publication. Evidence belongs under notes/evidence/kan-15-booking-action and notes/agent-reviews. Provisional interrupted attempts and corrected review findings must remain distinguished from final acceptance. H2/isolated Chromium scope, the inherited empty domain TODO and incomplete full access coverage remain explicit limitations.
