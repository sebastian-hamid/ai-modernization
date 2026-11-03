# Current-capability gate — first live checkpoint

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
