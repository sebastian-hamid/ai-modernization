# Independent review: KAN-15 ACTION-32 retirement evidence

- Reviewer: `/root/review_action32_evidence` (independent agent)
- Date: 2026-11-16
- Decision: **APPROVED for ACTION-32 RETIRED classification**. RETIRED is not PASS.
- Ticket: KAN-15
- Legacy action: rendered JSF destination-step `Next` command (`booking-date`)
- Replacement: `REPLACEMENT::booking-deadline`

## Scope and evidence reviewed

This review covers only the four ACTION-32 actor-specific stale-command observations and the evidence/validator changes needed to record them. It does not approve or re-review other retirement candidates. The browser run also included ACTION-08 actor observations; they passed the existing ACTION-08 validation and do not expand this approval.

Fresh aggregate gate evidence: `notes/evidence/kan-15-action32-retirement/current-capability-gate.json` (SHA-256 `971140884fa2afe35468272e9edb3cfc0f03cb6224b97fc53c5db0669ab99ee2`). The retained native fixture report `.work/kan18/results.json` (SHA-256 `0fc617aa0f868298e46caf3f63c5e3998cf76e513439cbfb40a43c77eaef7274`) reports PASS, 777/777 checks, owned-container removal, private-file removal and no cleanup errors. The retained Chromium report `.work/kan19/results.json` (SHA-256 `73c8e6f74a0b441a8c7362d8ae75638b6c9a851bc023a84fcfaadae763740e37`) contains 848/848 passed checks and all eight expected ACTION-32/ACTION-08 observations.

The actual legacy-rendered entry record `notes/evidence/kan-15-action32-retirement/legacy-rendered-entry.json` has SHA-256 `f3e959112d5072c28928bb270c85fd1b6cc78e5eca5b9d6f20e7207a01e38e5f`. It records a successful rendered destination view and the actual `Next` component/submission identifier `j_idt29:j_idt37`, action expression `booking-date`, and button-markup SHA-256 `b7a8ecbbe3ef616c45fd9ad9433b0ed5ef8470a5e154e8b5dba0e0d489be3d08`. Session, ViewState and client-window secrets are excluded. The record's four source hashes are checked against current source bytes by the verifier:

- Legacy destination page: `7cef897d90ba372ad4fe865778d211a084de8db302c0ac02aa14679944b441bb`
- Candidate booking page: `458a97585a67e1458358a5c846d4691e6d736981b31e0146de9fef7ed6e458ef`
- Compatibility navigation servlet: `e774a70a01f2cc7adb9d0c2a26dea6c14ad2ed800ebbec7df384d7730db502d4`
- Candidate access routes: `bd83abe21d3fb74411d7d27ed06e9cc75d937cf30d8ae021a7479c8c9169948c`

I reviewed the changed verifier, browser workflow, effects bridge, tests and capability mapping. Their SHA-256 values at review time were:

- `tests/browser-workflows/run_browser.py`: `50d6ec8635f1388671f72f6a9a67805fa980de4502a017cb9cb53faa54f79892`
- `tests/browser-workflows/workflows.cjs`: `bd10b1a7a529872e6e70493acc065eab8f134476b16d2c281952cec1c85c17fc`
- `tests/security/current_capabilities.py`: `ef03cd23732685e1f13a25b71d8962343b98c1451c81849fb8959bc967b5f925`
- `tests/browser-workflows/test_navigation_proofs.py`: `4f64d45d0d46beba90c77aa6c0e9cc879fce851faeb3ee982da42a7324dc93f4`
- `tests/security/test_current_capabilities.py`: `1a3196e35e784b7215e34b0cfabf284ded672a21421716078824b31013693dfb`
- `tests/browser-workflows/effects_bridge.py`: `112a7eb91847b0863806cb2805e6715442eebe1e8df8ee5cf5a7b4ec82215274`
- `tests/browser-workflows/test_effects_bridge.py`: `12f37e26636e37f430ec5e05bdf694c06ee6d3c477075e582f5fa426de53e7af`
- `specifications/current-capability-mapping-v2.json`: `173d22ff87d2e8c5ef42eb845ab766f8a3b0933e32a0ca7563af5bea04ed1f87`

Independent checks completed during review: 41 browser-workflow unit tests passed; 129 security unit tests passed; `git diff --check` passed. I independently ran the retirement-proof validator against the promoted observations in the fresh gate report; it passed.

## Actor results

All four requests used the historical destination path and exact rendered command identifier. The results were:

| Actor | Result | Session and effects evidence |
|---|---:|---|
| Anonymous | 303 to configured login | No identity, protected payload absent, effects unchanged |
| Reader | 403 | Server-verified Reader identity, protected payload absent, effects unchanged |
| Operator | 405 | Server-verified Operator identity; refreshed current form, CSRF and ViewState present; protected payload absent and effects unchanged |
| Administrator | 405 | Server-verified Administrator identity; refreshed current form, CSRF and ViewState present; protected payload absent and effects unchanged |

The 405 responses establish that the compatibility endpoint has no current POST handler for the retired command; they are not classified as authorization denials. All four actor-specific `REPLACEMENT::booking-deadline` cases are PASS. The four stale-command proofs share the same 13-cargo snapshot digest and record unchanged database, queue and business-invocation effects.

## Decision and limits

Approve the four ACTION-32 rows for **RETIRED**, never PASS, on the evidence above. The aggregate report correctly retains 470 current PASS, 16 previously reviewed RETIRED and 60 BLOCKED. Gate exit 2 is expected because those 60 other retirement cases remain blocked; it is not a failure of this ACTION-32 evidence.

The independent review does not cover the earlier ACTION-23 Administrator recheck regression: this focused browser run rechecked ACTION-32 and ACTION-08, not ACTION-23. It does not certify imported Python code identity; the run records `imported_code_attested=false`. The mapping still lists ACTION-32 as a candidate pending its evidence receipt/replay update. Do not change other retirement outcomes or current PASS results when applying that update. The fresh fixture and private credential files were confirmed cleaned up; shared Jenkins remained running.

## Follow-up review: finalized receipt and replay

- Date: 2026-11-16
- Decision: **APPROVED for commit** of the finalized ACTION-32 receipt, replay and mapping update.

I reviewed `notes/evidence/kan-15-action32-retirement/validation.json`, the pinned fresh `candidate-evidence.json`, native and browser result artifacts, the generated `current-capability-replay.json`, the ACTION-32 receipt verifier and replay implementation, and the current capability mapping. The receipt fails closed on changed proof/review/evidence hashes. The offline replay changes exactly the four ACTION-32 rows to RETIRED, leaves all current outcomes unchanged at 470 PASS, and preserves other retirement cases. The resulting counts are 20 RETIRED and 56 BLOCKED; gate exit 2 remains expected because the other 56 retirement cases are blocked. RETIRED is never PASS.

I reran the relevant offline tests: 41 browser-workflow tests and 131 security tests passed. I also ran the replay to a temporary output and verified its counts, gate exit and exact changed-case set; `git diff --check` passed.

This follow-up approves only the finalized ACTION-32 receipt/replay/mapping changes for commit. The earlier limitation remains: ACTION-23 Administrator was not rechecked by the focused browser run and remains outside this approval.
