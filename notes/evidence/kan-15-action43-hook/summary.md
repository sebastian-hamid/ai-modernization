# ACTION-43 old mobile initFlow hook proof

Date: 2026-11-17 (Europe/Bratislava)

## Result

The hook-specific proof verifies that the preserved historical `mobile.xhtml` contains the exact `<f:viewAction action="#{holderBean.initFlow}" />` binding. The candidate uses the same URL for its direct handling form, and a source-bound scan of every candidate Facelet finds no binding to `holderBean.initFlow`.

The proof reuses the fresh `kan15-handling-pages-d` fixture: 777 candidate checks and 970 browser checks passed; all 470 current capability cases passed; cleanup succeeded. At the same `/cargo-tracker/mobile.xhtml` URL, anonymous access redirected to login (303), Reader was denied (403), and Operator/Administrator received the current form (200) with server-verified identities. The authorized workflows verified dashboard entry, same-form fields, invalid calendar and missing-voyage rejection, leave navigation, and unchanged saved state. The page read effect was exactly one `CargoMonitoringService#getAllCargo` invocation per actor; tables and queues did not change.

## Important boundary

`HolderBean.initFlow()` and the old event-logger flow resources remain in the candidate source. This evidence proves that the old hook is no longer bound from candidate Facelets and that the replacement route works under the approved roles. It does not claim all old flow code was removed, nor does the fresh run instrument direct Java method invocation counts. The proof is from the synthetic candidate and makes no production claim.

Independent review approved this evidence as sufficient to retire only the old `initFlow` page hook as `RETIRED`. ACTION-43 remains `BLOCKED` until the user decides whether to apply that classification; `RETIRED` is never `PASS`. See the [review record](../../agent-reviews/2026-11-17-kan15-action43-hook-review.md).

## Evidence

- [Machine-readable validation](validation.json)
- Fresh source run: [candidate results](../kan-15-handling-page-retirement/candidate-runtime-results.json), [browser results](../kan-15-handling-page-retirement/browser-results.json), and [current-capability gate](../kan-15-handling-page-retirement/current-capability-gate.json)
- Reproduction: `python3 tests/security/action43_hook_proof.py`
- Regression checks: `python3 tests/security/test_action43_hook_proof.py`