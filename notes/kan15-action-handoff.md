# KAN-15 action coverage handoff

## Latest scoped checkpoint — 11 November 2026

KAN-15 remains In Progress. The fresh BG-06 scoped gate passed all five seed/reseed/schema-boundary cases (anonymous, Reader, Operator, Administrator, and deployment `schema_migrator`); evidence is `notes/evidence/kan-15-bg06-scope/validation.json`. An independently reviewed offline supplemental replay promotes only those rows, yielding 454 PASS / 16 BLOCKED while preserving the original 449/21 aggregate gate file, all other current outcomes, historical audit and retirement rows. It is not a new aggregate runtime run. Implementation/evidence are in `92aebd3`, status documentation in `6997a80`, and the supplemental replay in the current work. Review records: `notes/agent-reviews/2026-11-11-kan15-bg06-scope-review.md` and `notes/agent-reviews/2026-11-11-kan15-bg06-replay-review.md`.

This scoped result and replay do not rerun the full aggregate current-capability gate or close KAN-15. JMS destination-level authorization remains unverified because the probe did not send/consume messages. The BG-06 Administrator import route remains governed by BG-01/BG-02. Next: address the 16 remaining SERVICE-01 through SERVICE-04 actor cases, then run a fresh aggregate gate when the next bounded capability increment is ready, preserving the historical catalogue and separate RETIRED state.

## Historical checkpoint — 8 November 2026

KAN-15 remains In Progress. The latest fresh current gate is 424 PASS / 46 BLOCKED; the preserved historical audit is 324 PASS / 178 BLOCKED, and 76 retirement cases remain BLOCKED. ACTION-42 handling-completion verification passed all four actor cases and 661 native checks; the existing handling-event and handling-voyage role cases also remain PASS. Attempt 5 owned cleanup passed. Sanitized evidence is notes/evidence/kan-15-handling-completion/validation.json. Independent runtime/publication review is pending. Full security acceptance is incomplete.

The user explicitly approved specifications/current-ui-access-acceptance-proposal.md on 2 November 2026; see notes/decisions/2026-11-02-current-ui-acceptance.md. The versioned current-capability mapping and gate are implemented, retaining all 502 historical definitions and keeping RETIRED distinct from PASS. No retirement has been applied. Replacement and negative-entry evidence plus independent review remain mandatory; the 46 remaining current cases concern internal/worker capabilities and are not accepted by this decision.

KAN-26 is Done at febde7a4de7294ec6ff0d714cdd11e175b2ac341. The candidate protocol heartbeat keeps the original connection live beyond the measured 90-second listener timeout without HTTP renewal. Reset isolation, unrelated cargo persistence, normal close response and all-role logout/expiry were verified. General slow-peer/pool-saturation behavior remains unverified.

## Preserve and verify

Work in WSL Ubuntu-24.04 at /home/yasinrdp/projects/ai-modernization. Read AGENTS.md and docs/agent-review-workflow.md. Synced sources and experiments/legacy-cargotracker are read-only. Preserve shared ai-modernization-cargotracker, ai-modernization-jenkins and ai-modernization-baseline-agent containers. Fixtures own only their candidate/browser containers, private network and generated realm files.

Use a separate reviewer agent before publication. After independent approval and required checks, commit and push under standing authorization. The user superseded the blanket 30-minute cutoff on 2 November 2026. Use an independent progress monitor under docs/progress-monitoring.md; continue while measurable progress is being made, pause loops/stalled steps and retain bounded commands/retries. No new task window approval is required merely because 30 minutes elapsed.

The full fresh gate is:

    python3 tests/security/run_candidate_contracts.py --live-subset --output .work/kan15-next/catalogue-results.json

Exit2 is expected while unsupported cases remain. Require actual successful application/browser checks and complete cleanup as well as the bounded catalogue count. Never promote archived observations. Do not run a diagnostic second JVM inside the app container while the native effects observer is selecting its unique JVM.

## Remaining action priorities

ACTION-42 is now verified. Next priority is select the next still-blocked current capability action from the mapping and maintain the 46 internal/worker blockers; inspect gate IDs before choosing. There are no remaining blocked replacement-driver cases in the current gate. The 76 retirement checks remain BLOCKED.

All five write-behavior mappings are now bound: booking, destination change, initial/replacement route selection and handling submission. Forty active/logout/expiry definitions have independent per-POST effects and action-specific permitted controls. Handling additionally proves real core JMS add/ack, registration and inspection workers, and independent Reader state. Modern replacements already have real happy/invalid/Reader-forgery/CSRF browser scenarios, but those assertions alone do not satisfy every catalogue write definition.

The authoritative generator and checked inventory now explicitly mark all five mutation callbacks as POST. Regeneration is tested for exact equality; only method metadata changed in40 of502desired definitions, preserving IDs/roles/outcomes. A successful GET page render must never stand in for execution of a write callback. Preserve the approved roles and effects requirements when refining transport metadata.

For denied write promotion, the contract oracle requires settled independent database, queue and business-audit snapshots from the same fixture before and after the actual specific action request. Verify native role/session lifecycle and include a permitted positive control that demonstrably changes the intended state/worker channels. Do not reuse REST-handling denial evidence as proof of a different Faces booking/destination/routing action.

The host's existing lab-only AttachObserver and settled effects helpers are in tests/candidate-runtime/run_candidate.py. ACTION-29 reuses the native HTTP Faces form driver in the same process, so it can bracket actual POSTs directly without a browser coordinator or new observer endpoint. Prefer this proven integration for the next native form drivers where feasible. The browser callback still does not bracket each browser action with independent snapshots; do not claim otherwise.

Other remaining definitions include read-only legacy callbacks that need explicit modern-behavior mappings and trusted internal/worker drivers. Retired booking/mobile flow steps must not be counted as executed old callback code merely because their modern page opens. Document the equivalence or leave the case BLOCKED.

## Evidence locations

- docs/candidate/navigation-action-matrix.md: exact modern mappings and query restrictions.
- tests/browser-workflows/navigation-actions.json: shared reviewed mapping.
- tests/browser-workflows/run_browser.py: atomic proof promotion.
- tests/security/run_candidate_contracts.py: exact canonical case binding.
- notes/evidence/kan-15-navigation-actions: first six actions.
- notes/evidence/kan-15-routed-detail-action: routed-list detail action and current verification.
- notes/agent-reviews: independent review records.
- notes/setup-status.md: latest dated verified coverage, distinct from historical host setup.

- docs/candidate/booking-action-matrix.md and notes/evidence/kan-15-booking-action: exact POST mapping and booking effects/session proof.

- docs/candidate/destination-action-matrix.md and notes/evidence/kan-15-destination-action: exact target, preserved state and destination effects/session proof.

- docs/candidate/routing-action-matrix.md and notes/evidence/kan-15-routing-actions: exact selected/persisted itinerary, initial/replacement state and route effects/session proofs.

- docs/candidate/handling-action-matrix.md and notes/evidence/kan-15-handling-action: asynchronous submission/worker/state and session proofs.

- docs/candidate/handling-event.md and notes/evidence/kan-15-handling-event: ACTION-38 current event validation and exact persisted date/location/voyage association proof.

- docs/candidate/handling-voyage.md and notes/evidence/kan-15-handling-voyage: ACTION-39 known-voyage, invalid-voyage, and non-load association evidence, with shared ACTION-38 positive control disclosed.


- docs/candidate/handling-completion.md and notes/evidence/kan-15-handling-completion: ACTION-42 strict time validation, denied roles, composed positive control, bounded correlated misdirection effects and attempt history.


## Latest checkpoint  9 November 2026 (KAN-15 BG-05)

BG-05 notification consumers now use a dedicated `notification-worker` identity and generic identifier-free audit. The handling-attempt message TTL is 30 seconds (previously 1 second) to allow the configured 250 ms redelivery delay and retry deliveries to complete before expiry. The original full fresh run passed 723 native and 841 browser checks; its untouched gate artifact records 438 PASS / 32 BLOCKED and 76 retirement cases BLOCKED. Offline re-evaluation of six retained Operator/Administrator proofs for handling-event, handling-voyage and handling-completion corrects unrelated notification-audit overcounting: **444 PASS / 26 BLOCKED**. This is a re-evaluation, not a new runtime run. Four BG-05 human denials pass; BG-05 machine case remains blocked on external JMS/JNDI producer authorization. Browser audit evidence: one delivered, three misdirected, one rejection notification. Rejection-effect comparison now requires identical queue inventories as well as exact bounded queue/invocation deltas. Four focused comparator tests and 88 security unit tests pass. Cleanup passed and Jenkins stayed up. Independent final review pending. See [notification worker boundary](../docs/candidate/notification-worker-boundary.md), [original gate](evidence/kan-15-bg05-gate/current-capability-gate.json), and [offline replacement replay](evidence/kan-15-bg05-gate/replacement-gate-replay.json).
