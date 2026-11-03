# Booking and destination entry evidence

KAN-15, 3 November 2026. This increment addresses the 16 current-gate blocks identified in the [first live checkpoint](current-capability-gate.md). It changes test-fixture evidence production, preserving the application's role policy and historical contracts.

## Functional flow

Operator and Administrator load the real booking page before submitting its rendered form. For destination changes, they load details for their own selected cargo, follow its rendered Change destination link, verify the destination form, then submit the existing mutation driver.

Reader must not receive a booking form or a destination-edit link. The fixture verifies the Reader's authorized cargo details, checks the control is absent, then attempts the editor and forged POST directly. Anonymous source/editor GETs must redirect to the fixed local login with no cargo payload; the forged POST remains required. Existing independent per-POST database, queue and business-invocation comparisons remain in place.

For logout and expiry, the same authenticated opener owns and verifies the entry flow and rendered form before revocation. The fixture stores receipts by actor, lifecycle state and capability, then replays the saved form through the stale client. Entry verification is not reconstructed after revocation.

## Technical checks

The fixture reads the actual rendered destination link and accepts only the same origin, exact editor path and selected cargo. Unknown, duplicate and blank query fields, encoded paths/keys/cargo, raw backslashes and raw/decoded control characters are rejected. Valid percent encoding is permitted only within the optional Faces window query value. Receipts store the canonical source path and verification flag; a boolean records an encoded window query without retaining that value.

Pure helper regressions cover real-form requirements, wrong cargo/origin/target, unsafe/ambiguous links, exposed Reader controls, arbitrary login redirects, cargo leakage and failed editor loading. Unit doubles are test inputs, never runtime acceptance evidence.

The first integration attempt stopped after 244 passing native checks at an overbroad raw URI guard. Owned resources and private files were cleaned. The exact rejected href was not captured. A valid encoded-window regression reproduced over-rejection; the correction permits encoding only in the known window value, retaining strict target checks. Structural diagnostics and a value-free receipt flag make the next run inspectable.

## Verification

The fresh corrected run reports **324 PASS / 146 BLOCKED across 470 current cases**. All 16 ACTION-09/ACTION-29 actor/session cases pass with verified source receipts; six allowed destination-entry receipts record an encoded window query. The historical 502-case audit remains **324 PASS / 178 BLOCKED**, and all **76 retirement checks remain BLOCKED**. Gate exit is 2; KAN-15 is incomplete.

Native 565 and Chromium 431 checks passed. All owned application/browser containers, private network and credential files were removed without cleanup errors. The three shared baseline/historical/Jenkins containers remain running. Author verification passed 32 fixture and 54 security unit tests; the independent reviewer ran the 12 targeted booking/source-entry tests during correction review and inspected the final small guard changes without repeating that suite.

See [sanitized evidence](../../notes/evidence/kan-15-source-entry/validation.json) and [independent review](../../notes/agent-reviews/2026-11-03-kan15-source-entry-review.json). Full runtime/evidence publication assessment is recorded separately in that review file. The remaining current cases are 56 pending behaviors, 44 replacements and 46 internal/service/worker cases. No retirement is accepted.
