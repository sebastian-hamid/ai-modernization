# Claimed cargo list to details

ACTION-10 uses the existing disposable browser cargo after its CLAIM event persists. Reader, Operator and Administrator open its exact row in the claimed list. The browser verifies the local link and response for that cargo, compares the tracking ID, origin, destination and both statuses against a separate Reader API response, and checks the displayed date against the original booking deadline. The anonymous browser probes both protected URLs and verifies the configured login redirect without cargo data.

The fixture passed 652 native and 447 Chromium checks. All four ACTION-10 cases passed. The current gate is **348 PASS / 122 BLOCKED**. All 76 retirement checks remain blocked.

See the [sanitized results](../../notes/evidence/kan-15-claimed-cargo/validation.json) and [independent review](../../notes/agent-reviews/2026-11-04-kan15-claimed-cargo-review.json).
