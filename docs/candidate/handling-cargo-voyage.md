# Handling cargo and voyage evidence

This KAN-15 increment binds legacy callback ACTION-36 to the current mobile handling form. Operator and Administrator can select the fresh routed cargo and a known voyage (0100S). Submitting LOAD or UNLOAD without a voyage returns the validation message and does not write handling effects. The browser also submits forged, nonmember cargo and voyage values through the real form with its current view state. Both are rejected by the server and do not produce a successful submission.

Reader direct access returns 403, and anonymous access redirects to login. Neither response contains the protected cargo/voyage form values. The Operator and Administrator paths verify server principal and role independently.

Four actor cases passed. The fresh fixture passed 661 native checks and 725 browser checks. The database and queues remained unchanged across each before/after interval, and the independent cargo read was the only counted read delta. Current coverage moved from 404 PASS / 66 BLOCKED to 408 PASS / 62 BLOCKED. Historical audit remains 324 PASS / 178 BLOCKED. All 76 retirement cases remain BLOCKED. Owned application/browser containers, private files, and network were removed with no cleanup errors.

The runner fingerprints on-disk inputs and constructed contracts, but does not attest already-imported Python code identity. Raw browser output and detailed database snapshots remain private under `.work/`.

See [sanitized validation](../../notes/evidence/kan-15-handling-cargo-voyage/validation.json).
