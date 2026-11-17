# KAN-15 legacy handling page retirement evidence

Date: 2026-11-17 (Europe/Bratislava)
Run: `kan15-handling-pages-d` (fresh isolated candidate and browser fixtures)

## Result

- Candidate runtime: **777/777 checks passed**.
- Browser workflows: **970/970 checks passed**.
- Fresh pre-promotion gate: **470 current PASS, 64 RETIRED, 12 BLOCKED; exit 2**.
- Independent review approved ACTION-35 and ACTION-40. The offline, hash-pinned replay promoted exactly their eight actor/action rows to `RETIRED`. Final replay: **470 current PASS, 72 RETIRED, 4 BLOCKED; gate exit 2**. `RETIRED` never counts as `PASS`.
- The remaining four ACTION-43 actor rows are BLOCKED. `/mobile.xhtml` is the live replacement route, so URL denial is not appropriate; the user’s choice on hook-specific proof remains pending.
- Fixture-owned containers, network and credentials were cleaned up. Shared KAN-18 and Jenkins containers were left running and unchanged.

## Scope and evidence

The historical source controls are bound by markup and file hashes. The live browser accessed `/cargo-tracker/eventLogger/eventLogger.xhtml` for anonymous, Reader, Operator and Administrator actors and compared effects before/after:

- anonymous: HTTP 303 to the configured login route, no protected payload;
- Reader: HTTP 403, no protected payload;
- Operator and Administrator: HTTP 303 to the current `/mobile.xhtml` replacement; server identity, current form, and absence of the old single-page controls verified;
- no business/database/queue effect changes during these GETs.

Redirect acceptance resolves `Location` against the configured app URL and requires the same origin, exact application context plus expected route, no URL credentials, query or fragment. The proof stores base origin/context and raw Location; browser and offline validators check the destination. Negative tests reject cross-origin login/replacement URLs and wrong-context paths.

ACTION-35 is the historical Next navigation control. ACTION-40 is the historical Back navigation control. Both controls and their outcomes are hash-bound to the read-only historical source. The candidate legacy route mapping and current mobile replacement are also hash-bound.

## Independent review

The separate reviewer initially requested changes because redirect validation accepted suffix matches without verifying origin/context. The implementation was corrected and re-reviewed. Final verdict: **Approved for ACTION-35/ACTION-40** with no remaining material findings. Review record: `notes/agent-reviews/2026-11-17-kan15-handling-page-retirement-review.md`.

The final promotion diff, mapping, hash-pinned receipt and offline replay received a second independent approval with no material findings. The reviewer confirmed exact row scope, preservation of all other rows, and that `RETIRED` never becomes `PASS`.

Focused verification: **87 tests passed** (`tests.browser-workflows.test_navigation_proofs` and `tests.security.test_current_capabilities`); Python compile checks and `git diff --check` passed. The fresh live browser run executed the updated JavaScript workflow.

## Files and SHA-256

- `current-capability-gate.json`: `96c59c67f207af4cd5d6fb8364e4a7a3471c1fac339abe0534737ca36f72a74e`
- `candidate-runtime-results.json`: `637f8b53c5a52c5e799b99516ffa8136492cbbb39110ab63845f6e69bc3f8ff1`
- `browser-results.json`: `eac9cf910aa529352709d74952d6e068a7aa8c5044f96c5ddf0f2825543609f6`
- `promotion-validation.json`: `ce8cff40e1075f0b48524b3af799ba344f2333401ff4ce00b3122d2957e38981`
- `current-capability-replay.json`: `6e8558470a2f12a81207e402aecb5d4db766959c20e4f97b62fc8d84cab1d982`

The full run files remain under ignored `.work/kan15-handling-pages-d/`. The receipts above are saved here. Only ACTION-35/ACTION-40 mapping rows were promoted; ACTION-43 remains blocked pending user decision.

## Remaining project status

KAN-15 remains In Progress. Its broader gate still has four BLOCKED ACTION-43 rows and other acceptance work; this promotion does not close the Jira issue.


