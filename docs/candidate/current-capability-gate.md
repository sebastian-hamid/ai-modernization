# Current-capability gate — first live checkpoint

## Latest scoped boundary update — 11 November 2026

A separate fresh BG-06 gate passed all five seed/reseed/schema-boundary cases: the four human denials and the deployment `schema_migrator` Flyway case. Its persisted evidence is [notes/evidence/kan-15-bg06-scope/validation.json](../../notes/evidence/kan-15-bg06-scope/validation.json). An [offline supplemental replay](../../notes/evidence/kan-15-bg06-scope/current-capability-replay.json) combines only those five results with the 9 November aggregate snapshot: 449 PASS / 21 BLOCKED becomes 454 PASS / 16 BLOCKED. It records hashes for the untouched current rows, historical audit and retirement rows; it does not rewrite the source gate or claim a new full runtime run. KAN-15 remains In Progress, and the BG-06 remote JMS probe did not test destination-level send/consume authorization.

KAN-15, 2 November 2026. Approved acceptance direction: [decision](../../notes/decisions/2026-11-02-current-ui-acceptance.md). Runtime/test inputs were frozen at commit 7186ab9 throughout this first v2 integration run.

The versioned gate reports **308 PASS / 162 BLOCKED across 470 current cases**. All **76 retirement checks remain BLOCKED**. The same fresh fixture reports the preserved historical catalogue as **324 PASS / 178 BLOCKED across 502 cases**. Gate exit is 2: incomplete coverage. No legacy definition has been deleted or relabeled PASS/RETIRED.

## Evidence and verification

The disposable native fixture passed 565 checks; Chromium passed 431 checks. Owned application/browser containers, private network and credential files were removed with no cleanup errors. Shared baseline-agent, historical Cargo Tracker and Jenkins containers remain running. See [sanitized evidence](../../notes/evidence/kan-15-current-capability-gate/validation.json).

The separate reviewer independently inspected all six checkpoint files, verified their hashes and ran 54 security unit tests successfully. It also replayed the fresh observations without launching another fixture: all current, legacy and retirement result arrays match, as do input and contract fingerprints. Cleanup was checked through recorded evidence, not independently observed during execution. This establishes the scoped scaffold and first integration checkpoint; it does not complete KAN-15.

## Remaining work

| Current cases still BLOCKED | Count | Next requirement |
| --- | ---: | --- |
| Booking/destination source provenance | 16 | Record actual verified entry flow; do not infer source metadata from a POST target. |
| Pending current-equivalent behaviors | 56 | Implement the 14 approved drivers for all four actors. |
| Replacement capabilities | 44 | Implement the 11 explicit capability drivers for all four actors. |
| Internal/service/worker boundaries | 46 | Implement scoped independent adapters and effects/security evidence. |

Booking ACTION-29 and destination ACTION-09 still pass their historical POST contracts, but all 16 actor/session observations lack the stronger current source evidence. The destination mapping requires entry through the selected cargo's details (admin/show.xhtml); the existing producer directly fetches the destination form. A metadata-only patch would misrepresent that flow.

Retirement is separate: none of the 76 checks has a supported fresh replacement/negative-entry/review verifier. RETIRED is never PASS. Role, revocation, CSRF, payload and independent denied-write effects remain required. The provenance fingerprint covers on-disk inputs and constructed contracts, with imported-code identity explicitly unattested.

## Run

From the WSL repository root:

    python3 -m unittest discover -s tests/security -p 'test_*.py'
    python3 tests/security/run_current_capabilities.py --live-subset --output .work/kan15-current-capabilities/results.json

The live command owns a fresh native/browser fixture and requires Docker plus existing build dependencies. Missing adapters remain BLOCKED; default execution without --live-subset executes no fixture and blocks all cases. Do not reuse old .work results to assert a new runtime run.

## Subsequent source-entry verification — 3 November 2026

The [source-entry increment](source-entry-evidence.md) resolves the 16 booking/destination provenance gaps above using actual source GETs, destination links and saved pre-revocation receipts. Latest current results are **324 PASS / 146 BLOCKED**; the historical audit remains 324/178 and retirement remains 76 BLOCKED. The earlier 308/162 result is preserved as the first checkpoint, not the current total.

## Subsequent current load behaviors — 3 November 2026

[Destination-form and cargo-details loads](current-load-behaviors.md) add eight specifically verified current GET cases. Latest current totals: **332 PASS / 138 BLOCKED**. Historical audit remains324/178; retirement remains76BLOCKED. These current capabilities do not claim execution of the original framework callbacks.

## Route choices and itinerary alias — 4 November 2026

[Current route choices](current-route-choices.md) add eight ACTION-16/ACTION-18 cases. Current gate **340 PASS / 130 BLOCKED**. Historical audit 324/178 and retirement 76 BLOCKED remain unchanged. The selected cargo details were verified in the subsequent ACTION-15 checkpoint.

ACTION-15 adds four [route cargo details cases](current-route-choices.md#selected-cargo-details). The current gate is **344 PASS / 126 BLOCKED**.

ACTION-10 adds four [claimed cargo navigation cases](current-claimed-cargo.md). The current gate is **348 PASS / 122 BLOCKED**.

The [unrouted and routing entry group](current-cargo-entries.md) adds 16 cases for ACTION-11/12/21/22. Current gate **364 PASS / 106 BLOCKED**.

The [return and tracking increment](current-return-and-tracking.md) verifies ACTION-13/24/25/45. Current gate **380 PASS / 90 BLOCKED**. Remaining current blocks comprise 44 replacement and 46 internal cases.

The [initial replacement capabilities](replacement-capabilities.md) add 12 cases for cancellation and tracking discovery. Current gate **392 PASS / 78 BLOCKED**.

The [booking replacement increment](booking-replacement-capabilities.md) adds eight cases for strict deadline validation and the single-page booking flow. Current gate **400 PASS / 70 BLOCKED**. The remaining current cases are 24 replacement cases and 46 internal-boundary cases.

## Handling event increment — 8 November 2026

The [ACTION-38 handling-event increment](handling-event.md) adds four current role cases. The fresh native/browser fixture passed 661 native and 779 browser checks with owned cleanup. Current gate: **416 PASS / 54 BLOCKED**. Historical audit remains 324 PASS / 178 BLOCKED and all 76 retirement cases remain BLOCKED. The live gate exits 2 while that inventory is blocked; it is not the fixture result. See [sanitized validation](../../notes/evidence/kan-15-handling-event/validation.json).

## Handling voyage increment — 8 November 2026

The [ACTION-39 handling-voyage increment](handling-voyage.md) adds four current role cases. The fresh native/browser fixture passed 661 native and 791 browser checks with owned cleanup. Current gate: **420 PASS / 50 BLOCKED**. Historical audit remains 324 PASS / 178 BLOCKED and all 76 retirement cases remain BLOCKED. The proof reuses the same-fixture ACTION-38 positive event observation and does not claim an additional event submission. See [sanitized validation](../../notes/evidence/kan-15-handling-voyage/validation.json).


## Notification workers  -  9 November 2026 (KAN-15 BG-05)

The original fresh current-capability gate recorded **438 PASS / 32 BLOCKED**; all **76 retirement** cases remain BLOCKED. The run passed 723 native and 841 browser checks, with owned cleanup verified. An offline re-evaluation of six retained Operator/Administrator proofs for handling-event, handling-voyage and handling-completion yielded **444 PASS / 26 BLOCKED**. Those older proofs observed zero misdirected-queue deliveries and zero corresponding notification audit events. This replay did not launch a fixture and did not replace the original gate artifact or its fingerprint. BG-05's four human actor denials pass. Its server-worker machine case was still BLOCKED pending external JMS/JNDI producer authorization; that state is superseded by the 9 November producer-boundary refresh below. See the [original sanitized gate](../../notes/evidence/kan-15-bg05-gate/current-capability-gate.json), [offline replay](../../notes/evidence/kan-15-bg05-gate/replacement-gate-replay.json), and [worker boundary](notification-worker-boundary.md).

The full browser workflow generated one delivered, three misdirected, and one rejected-registration worker audit events; see [sanitized audit lines](../../notes/evidence/kan-15-bg05-gate/notification-audit-lines.log). The native fixture's rejection snapshot proves exactly three total input deliveries (initial plus two retries), one broker DLQ transfer, one rejection-queue acknowledgment, unchanged database hashes, and the exact bounded queue/invocation deltas. The corrected comparator requires identical before/after queue names and counters; unrelated queue additions, counter changes and invocation changes fail. Security unit suite at this run: 88 PASS; focused comparator tests: 4 PASS. The handling-audit oracle and BG-01 machine-verifier regressions bring the current security unit suite to 90 PASS. Evidence: [rejection replay record](../../notes/evidence/kan-15-bg05-gate/rejection-delta-replay.json).


## BG-05 producer boundary and gate refresh — 9 November 2026

A separate-JVM remote+http JMS probe now verifies the trusted handling-attempt producer boundary. The fresh integrated candidate/browser fixture passed 722/722 checks, and the security unit suite passed 88 tests at that run. The raw fresh gate is **439 PASS / 31 BLOCKED**; BG-05-MACHINE is PASS. A subsequent offline re-evaluation of six same-fixture handling-event, handling-voyage and handling-completion Operator/Administrator proofs plus BG-01-MACHINE yields **446 PASS / 24 BLOCKED**. The handling proofs show one handling-attempt publication, one MisdirectedCargoQueue delivery, one MisdirectedCargoConsumer invocation and one matching NotificationWorkerAudit invocation; older samples show zero misdirected deliveries and audit events. The oracle requires one publication when that invocation metric exists, and makes the notification-audit delta equal the observed misdirected-delivery delta. The BG-01 proof separates the Administrator initiator from the server-verified batch-worker principal and BatchWorker role, and confirms valid/invalid file handling. This preserves the fresh gate's fingerprint and raw results; it is supplemental offline evaluation, not a replacement runtime run. Historical audit remains **324 PASS / 178 BLOCKED**, and all **76 retirement cases remain BLOCKED**. Gate exit 2 reflects other unsupported current and retirement cases; it is not a fixture failure. Fixture and gate cleanup were verified. See the [sanitized validation evidence](../../notes/evidence/kan-15-bg05-producer-boundary/validation.json), [latest same-run replay](../../notes/evidence/kan-15-bg05-producer-boundary/replacement-gate-replay.json), [producer boundary design](notification-worker-boundary.md), and [batch worker boundary](batch-import-worker-boundary.md).

## Handling worker producer boundary — 9 November 2026 (KAN-15 BG-03)

The fresh remote+http JMS probe verifies the trusted handling-attempt-producer can enqueue, while anonymous, Reader, Operator, Administrator, BatchWorker, HandlingWorker, InspectionWorker, and NotificationWorker cannot send to the attempt queue. It also verifies the trusted producer cannot send to the rejection or delivered-notification queues. Authentication is forced before authorization checks and only explicit JMS security denial from the send call counts. The gate validates the raw named-principal arrays and denial results alongside same-fixture server-side handling-worker identity and authorized adapter events.

Fresh native/browser fixture: **722 native checks** and **841 browser checks** passed; cleanup removed the owned container and credentials. Current gate: **447 PASS / 23 BLOCKED**; historical audit **324 PASS / 178 BLOCKED**; all **76 retirement checks remain BLOCKED**. BG-03-MACHINE is PASS. The remaining current blockers are BG-02-MACHINE, BG-04-MACHINE, BG-06 (four human cases plus deployment/migration machine case), and SERVICE-01 through SERVICE-04 (all four actors each). Gate exit 2 is expected while those cases remain unsupported. See the sanitized validation and current gate under notes/evidence/kan-15-bg03-producer-boundary, and docs/candidate/handling-worker-boundary.md.


## Cargo inspection producer boundary  -  9 November 2026

The [BG-04 producer-boundary increment](handling-worker-boundary.md#bg-04-cargo-inspection-producer-boundary) verifies the CargoHandledQueue broker ACL from a separate JVM. The fixture allows the credential-verified HandlingWorker account to attempt a transacted send and rolls it back; it denies anonymous, Reader, Operator, Administrator, BatchWorker, InspectionWorker, and NotificationWorker. The fixture checks that database state, CargoHandledQueue counters, inspection invocation count, and inspection audit count remain unchanged by this authorization probe.

The fresh native fixture passed **724 checks** and Chromium passed **841 checks**. Current gate: **448 PASS / 22 BLOCKED**; historical audit: **324 PASS / 178 BLOCKED**; retirement: **76 BLOCKED**. CURRENT::BG-04-MACHINE::worker-BG-04::active is PASS. Remaining current blockers are BG-02-MACHINE; BG-06 for four human actors and deployment/migration machine authority; and SERVICE-01 through SERVICE-04 for all four actors. Exit 2 remains expected because coverage is incomplete. Source fingerprint: `a656082f4193d00de715d2a048a72167aceff02a4838802b370d7feebd5360d3`. See [sanitized validation](../../notes/evidence/kan-15-bg04-producer-boundary/validation.json) and [current gate](../../notes/evidence/kan-15-bg04-producer-boundary/current-capability-gate.json).


## Trusted batch filesystem boundary — 9 November 2026 (KAN-15 BG-02)

The fresh disposable fixture verifies approved administration tooling as the trusted staging producer and the WildFly server OS identity (UID 1000) as the filesystem owner. Mode-700 incoming, archive, and failed directories deny UID 65534 listing, reading, and writing; no marker files remain. A valid staged event is persisted and archived, while a malformed input is isolated in failed output. The native fixture passed 728 checks and Chromium passed 841. BG-02-MACHINE is PASS. The complete gate reports **449 PASS / 21 BLOCKED** current cases, **324 PASS / 178 BLOCKED** historical cases, and **76 BLOCKED** retirement cases. Exit 2 remains expected while unrelated blocked inventory exists. Fingerprint: `5f855b30bfca64555a04421e9ed7569b6732844db8c54357bb087aa6bb7b3113`. See [sanitized validation](../../notes/evidence/kan-15-bg02-filesystem-boundary/validation.json), [full current gate](../../notes/evidence/kan-15-bg02-filesystem-boundary/current-capability-gate.json), and [boundary notes](batch-import-worker-boundary.md).
