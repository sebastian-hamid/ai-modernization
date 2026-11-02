# KAN-15 action coverage handoff

## Current verified checkpoint

KAN-15 remains In Progress. Current fresh coverage is292PASS/210BLOCKED: seven navigation mappings (28 cases) plus ACTION-29 booking (eight active/logout/expiry cases). Booking verification passed411application/431browser checks,35reported domain cases(one inherited emptyTODO),68tooling checks. Evidence is notes/evidence/kan-15-booking-action; independent review records are under notes/agent-reviews. Remaining210 contracts comprise148active actions(132read-only/16write),16write-action session cases and46internal/worker definitions. This is not full security acceptance.

KAN-26 is Done at febde7a4de7294ec6ff0d714cdd11e175b2ac341. The candidate protocol heartbeat keeps the original connection live beyond the measured 90-second listener timeout without HTTP renewal. Reset isolation, unrelated cargo persistence, normal close response and all-role logout/expiry were verified. General slow-peer/pool-saturation behavior remains unverified.

## Preserve and verify

Work in WSL Ubuntu-24.04 at /home/yasinrdp/projects/ai-modernization. Read AGENTS.md and docs/agent-review-workflow.md. Synced sources and experiments/legacy-cargotracker are read-only. Preserve shared ai-modernization-cargotracker, ai-modernization-jenkins and ai-modernization-baseline-agent containers. Fixtures own only their candidate/browser containers, private network and generated realm files.

Use a separate reviewer agent before publication. After independent approval and required checks, commit and push under standing authorization. The user superseded the blanket 30-minute cutoff on 2 November 2026. Use an independent progress monitor under docs/progress-monitoring.md; continue while measurable progress is being made, pause loops/stalled steps and retain bounded commands/retries. No new task window approval is required merely because 30 minutes elapsed.

The full fresh gate is:

    python3 tests/security/run_candidate_contracts.py --live-subset --output .work/kan15-next/catalogue-results.json

Exit2 is expected while unsupported cases remain. Require actual successful application/browser checks and complete cleanup as well as the bounded catalogue count. Never promote archived observations. Do not run a diagnostic second JVM inside the app container while the native effects observer is selecting its unique JVM.

## Remaining action priorities

ACTION-29 booking is now bound with independent per-POST effects, native role/session checks and permitted booking-specific controls. Remaining original write callbacks are ACTION-09 destination change, ACTION-17/ACTION-19 route selection and ACTION-41 handling submission:16active actor and16logout/expiry definitions. Modern replacements already have real happy/invalid/Reader-forgery/CSRF browser scenarios, but those assertions alone do not satisfy every catalogue write definition.

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
