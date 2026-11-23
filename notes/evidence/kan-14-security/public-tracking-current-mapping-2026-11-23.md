# KAN-14 public tracking: historical and current expectations

Date: 2026-11-23
Current candidate source: a20c212.

## Reconciliation

The seven PAGE-25 FAIL outcomes in the 23 November KAN-14 contract report remain accurate for the historical catalogue: anonymous access and logged-out/expired sessions for Reader, Operator and Administrator contradict the original KAN-12 deny expectation. Preserve those historical FAIL rows and the original inventory.

The approved current-capability model separately maps PAGE-25 and ACTION-45 to the public, read-only typed tracking capability at /cargo-tracker/public/track.xhtml, with anonymous access allowed. Its approval is recorded in notes/decisions/2026-11-02-current-ui-acceptance.md; the model is specifications/current-capability-mapping-v2.json. tests/security/test_current_capabilities.py::test_public_typed_tracking_overrides_only_current_page_access_and_survives_revocation asserts the historical PAGE-25 anonymous expectation remains deny, while the current PAGE-25 cases are allow and logged-out access remains public after revocation.

A fresh isolated candidate runtime on source a20c212 recorded 10 PAGE-25 observations: anonymous plus Reader/Operator/Administrator while active, and all three roles after logout and expiry. All returned HTTP 200 with the typed tracking semantics verified and protected fixture payloads absent. The six logged-out/expired observations also recorded public_access_after_revocation=true and revocation_verified=true. Raw receipt: ignored .work/kan18-kan23-history-20261123/candidate-runtime/results.json, SHA-256 617a1bd9504f972aeccb8cbb73b41f26ec28dd98ea1e003e60ff8774f2ba09dd; the run summary is [KAN-18 candidate regression](../kan18-kan23-history-regression/README.md).

## Status

This resolves how to interpret the seven historical failures; it does not relabel or remove them. The current approved contract is public, typed, read-only tracking and the current candidate observations match it. No new user decision is required for this discrepancy because the current capability mapping and its approval already state this policy.

KAN-14 remains In Review. The 178 unsupported adapter rows from the live-subset catalogue remain BLOCKED, and this reconciliation does not claim their coverage or close the ticket. Independent review approved with no material discrepancies: [review record](../../agent-reviews/2026-11-23-kan14-page25-reconciliation-review.md).
