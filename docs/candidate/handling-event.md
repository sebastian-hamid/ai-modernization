# Handling event evidence

This KAN-15 increment binds legacy callback ACTION-38 to the current mobile handling form. The browser runs as anonymous, Reader, Operator, and Administrator. Anonymous access redirects to login; Reader receives 403. Operator and Administrator see the current supported event choices, invalid event values are rejected, and LOAD and UNLOAD are rejected without a voyage.

For the positive path, the workflow selects voyage 0100S, switches from LOAD to CUSTOMS, confirms the UI retains the selected voyage, then submits. A bounded, read-only JMX observer queries the disposable ExampleDS using the booked cargo tracking ID, persisted date, CUSTOMS type, and actor-specific location. It returns exactly one row for each actor. Both persisted CUSTOMS rows have a null voyage association, and the cargo remains routed.

The legacy entity maps completionTime as SQL DATE. The form accepts an hour and minute, but persistence retains the date at midnight; the evidence verifies the stored date and does not claim hour precision. Operator and Administrator use different locations to identify the exact row for the shared persisted date.

All four actor cases passed. The fresh fixture passed 661 native and 779 browser checks. The current gate moved from 412 PASS / 58 BLOCKED to 416 PASS / 54 BLOCKED. The preserved historical audit remains 324 PASS / 178 BLOCKED, and all 76 retirement cases remain BLOCKED. Gate exit 2 reports this incomplete remaining inventory; the native/browser fixture itself passed. Owned application and browser containers, private files, and network were removed with no cleanup errors.

Two earlier fresh attempts were not promoted. Attempt 1 recorded 472 browser checks and stopped when the Operator-after effects snapshot timed out; attempt 2 stopped at an overly restrictive observer selector guard that compared the browser-created cargo with a different native seed cargo. Both attempts completed cleanup. The corrected successful run uses a bounded read-only query and binds the returned row to the same browser-created ID in the proof. See the sanitized [validation](../../notes/evidence/kan-15-handling-event/validation.json).

The fixture fingerprints on-disk inputs and constructed contracts, not identity of already-imported Python code. Raw browser output and full database snapshots remain private under .work/. This is not complete security acceptance or production deployment.
