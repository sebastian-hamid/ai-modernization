# Handling voyage evidence

This KAN-15 increment binds legacy callback ACTION-39 to voyage behavior on the current mobile handling form. Operator and Administrator can see and select the known voyage 0100S. The real form rejects a forged voyage value and rejects LOAD and UNLOAD when no voyage is selected.

The non-load path selects 0100S, changes the event to CUSTOMS, confirms the form still displays the selected voyage, then uses the already-submitted same-fixture ACTION-38 positive control. A bounded read-only observer returns exactly one persisted CUSTOMS row for the same booked cargo, date and actor-specific location, with a null voyage association. This ACTION-39 proof combines those same-actor/same-cargo observations; it does not claim a second event submission.

The entity stores completionTime as SQL DATE. The persisted date is therefore reported at midnight; no hour-precision claim is made.

All four actor cases passed. Anonymous access redirected to login, Reader received 403, and neither received protected form data. The fresh fixture passed 661 native and 791 browser checks. Current coverage moved from 416 PASS / 54 BLOCKED to 420 PASS / 50 BLOCKED. The historical audit remains 324 PASS / 178 BLOCKED; all 76 retirement checks remain BLOCKED. Gate exit 2 reflects this remaining inventory, not a fixture failure. Owned app/browser containers, private files and network were removed with no errors.

See the sanitized [validation](../../notes/evidence/kan-15-handling-voyage/validation.json). Raw browser output and detailed effect samples remain private under .work/. The current gate fingerprint does not attest already-imported Python code identity. Full security acceptance and production deployment are still out of scope.
