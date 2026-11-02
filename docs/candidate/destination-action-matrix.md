# KAN-15 destination-change action matrix

Scope: eight ACTION-09 cases, mapping the historical destination-change callback to the current native Faces POST at /cargo-tracker/admin/changeDestination.xhtml?trackingId=<cargo>. It does not claim the retired dialog/backing callback executes. Existing role policy and business rules are unchanged.

## Form and independent observations

The native driver loads a real form with the caller's permitted cargo ID, CSRF token and ViewState. The shared denial observer now accepts an explicit action path; the booking wrapper retains its previous path and behavior. Each denied destination POST has its own settled before/after SQL content hashes, cumulative Artemis counters and EJB/MDB audit snapshots. Anonymous must receive the configured local 303 login redirect; Reader must receive 403; no cargo payload or independent state change is allowed.

Operator and Administrator each change only their own freshly booked, unreceived control cargo from FIHEL to USNYC. Real local 302/303 result redirects must preserve the exact tracking ID. A separate Reader verifies the destination, unchanged origin/routing/transport/location, unchanged arrival deadline and unchanged cargo ID set; every unrelated cargo must remain identical. SQL content must change, the changeDestination business invocation delta must be exactly one and queues must remain unchanged. This action does not produce JMS messages, so no worker event is invented.

For logout and idle expiry, each role loads and saves its own destination form before native revocation. Replay submits FIHEL while the cargo currently has USNYC, providing genuine mutation intent. Real logout or at least 75 seconds without HTTP activity precedes saved-cookie/form POSTs. The existing lifecycle check verifies server identity 401; each replay must redirect to the configured local login, leak no cargo and leave all independent channels unchanged.

## Binding and tests

Only canonical ACTION-09/PAGE-04/POST/write callback definitions are added. Proofs must identify the exact modern cargo query and POST path, actual form and pre-revocation form ownership. Positive binding additionally requires concrete redirect status, SQL change, exactly one destination invocation, independent Reader persistence/deadline and unchanged unrelated cargos. A changed target, missing observer channel, arbitrary success flag or altered canonical contract cannot substitute.

Focused tests cover real-form requirements and replay intent, missing/wrong SQL/audit/queue effects, multiple invocations, wrong cargo/origin/destination/transport state, cargo query mismatch, incomplete positive evidence and mutated session contracts. All previous booking, API/page/socket and browser regressions run with the fresh fixture. No observer endpoint or browser coordination protocol is added.

Run from WSL:

    python3 tests/security/run_candidate_contracts.py --live-subset --output .work/kan15-destination-action/catalogue-results.json

## Acceptance boundaries

Fresh execution passed eight destination cases and all prior bindings: 442 application checks, 431 Chromium checks and 72 tooling checks. The 35 reported domain cases retain one inherited empty TODO. Current catalogue: 300 PASS / 202 BLOCKED, native exit 2. App/browser/network/private files were removed. Evidence is under notes/evidence/kan-15-destination-action, with independent review recorded before publication. Full security acceptance remains incomplete; unsupported catalogue definitions still yield native exit 2. The isolated H2/Chromium fixture and one inherited empty domain TODO remain disclosed. Task resources and private files must be removed, with historical source/runtime and shared Jenkins preserved. No production deployment is included.
