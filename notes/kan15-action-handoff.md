# KAN-15 action coverage handoff

## Current verified checkpoint

KAN-15 remains In Progress. Published 18098b8548e7ff1c65f233ead643a81fb9240724 has 280 PASS / 222 BLOCKED desired contracts: ACTION-01 through ACTION-06 cover 24 active actor cases. Its fresh evidence has 367 application checks, 417 browser checks, 35 reported domain cases (one inherited empty TODO) and 60 tooling checks. Independent review approved publication. ACTION-14 routed-list details now additionally passed four fresh cases. Current coverage is284PASS/218BLOCKED, with367application/431browser/35reported domain cases(one inherited emptyTODO) and61tooling checks. Its evidence is notes/evidence/kan-15-routed-detail-action. Remaining218 contracts comprise152active actions(132read-only and20write),20write-action session cases and46internal/worker definitions. Publication requires the separate review record.

KAN-26 is Done at febde7a4de7294ec6ff0d714cdd11e175b2ac341. The candidate protocol heartbeat keeps the original connection live beyond the measured 90-second listener timeout without HTTP renewal. Reset isolation, unrelated cargo persistence, normal close response and all-role logout/expiry were verified. General slow-peer/pool-saturation behavior remains unverified.

## Preserve and verify

Work in WSL Ubuntu-24.04 at /home/yasinrdp/projects/ai-modernization. Read AGENTS.md and docs/agent-review-workflow.md. Synced sources and experiments/legacy-cargotracker are read-only. Preserve shared ai-modernization-cargotracker, ai-modernization-jenkins and ai-modernization-baseline-agent containers. Fixtures own only their candidate/browser containers, private network and generated realm files.

Use a separate reviewer agent before publication. After independent approval and required checks, commit and push under standing authorization. Keep the same task timer across increments: stop by 30 minutes, record exact state and wait for user input; do not reset an incomplete ticket's timer through sub-increments.

The full fresh gate is:

    python3 tests/security/run_candidate_contracts.py --live-subset --output .work/kan15-next/catalogue-results.json

Exit2 is expected while unsupported cases remain. Require actual successful application/browser checks and complete cleanup as well as the bounded catalogue count. Never promote archived observations. Do not run a diagnostic second JVM inside the app container while the native effects observer is selecting its unique JVM.

## Remaining action priorities

Five original write callbacks are ACTION-09 destination change, ACTION-17/ACTION-19 route selection, ACTION-29 booking and ACTION-41 handling submission. They account for 20 active actor and 20 logout/expiry definitions. Modern replacements already have real happy/invalid/Reader-forgery/CSRF browser scenarios, but those assertions alone do not satisfy every catalogue write definition.

The generator currently gives callback descriptors a default GET method when the inventory row has no method; existing modern Faces mutation drivers actually submit POST. Treat this as a descriptor/driver mapping gap to resolve and independently review before write binding. A successful GET page render must never stand in for execution of a write callback. Preserve the approved roles and effects requirements when refining transport metadata.

For denied write promotion, the contract oracle requires settled independent database, queue and business-audit snapshots from the same fixture before and after the actual specific action request. Verify native role/session lifecycle and include a permitted positive control that demonstrably changes the intended state/worker channels. Do not reuse REST-handling denial evidence as proof of a different Faces booking/destination/routing action.

The host's existing lab-only AttachObserver and settled effects helpers are in tests/candidate-runtime/run_candidate.py. The browser callback currently does not bracket each browser action with those snapshots. A host/browser checkpoint coordinator is a possible implementation approach, not an implemented or verified capability. Preserve isolation and avoid exposing a new observer endpoint or secrets.

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
