# Unrouted cargo and routing entry

ACTION-11 starts on the unrouted list, follows the selected cargo to details, then follows its route link. ACTION-12 follows the same list and details chain to the destination editor and verifies the current destination. ACTION-21 verifies initial route entry from the selected details page. ACTION-22 verifies replacement route entry after routing has persisted.

Operator and Administrator use their own booked cargo. A separate Reader API response verifies the required routing state. Each target link and navigation response must identify the exact local cargo. Reader source pages expose the selected cargo but hide the editing controls, and direct requests to the targets receive 403. Anonymous source and target requests receive the fixed login redirect without cargo data.

The fresh fixture passed 652 native and 507 browser checks and 80 unit checks. All 16 current cases passed, taking the current gate to **364 PASS / 106 BLOCKED**. Historical coverage is 324 PASS / 178 BLOCKED, and all 76 retirement checks remain BLOCKED. Gate exit is 2.

See [sanitized evidence](../../notes/evidence/kan-15-cargo-entries/validation.json) and [independent review](../../notes/agent-reviews/2026-11-05-kan15-cargo-entries-review.json). Runtime cargo IDs and raw response bodies are omitted from publication.
