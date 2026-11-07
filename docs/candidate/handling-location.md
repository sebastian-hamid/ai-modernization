# Handling location evidence

This KAN-15 increment binds legacy callback ACTION-37 to the current mobile handling form. Operator and Administrator can see and select a known location (USCHI). Reader direct access returns 403, and anonymous access redirects to login without protected form data.

The fresh browser submits the real form twice with browser-native validation bypassed. A missing required location is rejected by server-side JSF validation. A forged nonmember location is rejected by select-item validation or the controlled handler error. Neither response shows the accepted-for-processing message. Independent before/after snapshots confirm no database or queue changes and only the final cargo read delta.

All four actor cases passed. The fixture passed 661 native checks and 749 browser checks, with owned cleanup verified. Current coverage moved from 408 PASS / 62 BLOCKED to 412 PASS / 58 BLOCKED. Historical audit remains 324 PASS / 178 BLOCKED. All 76 retirement cases remain BLOCKED.

The runner fingerprints on-disk inputs and constructed contracts but does not attest already-imported Python code identity. Raw browser output and detailed snapshots remain private under `.work/`.

See [sanitized validation](../../notes/evidence/kan-15-handling-location/validation.json).
