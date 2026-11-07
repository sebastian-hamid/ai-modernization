# Single-page handling capability evidence

This KAN-15 increment binds the legacy handling entry points to the current authenticated mobile handling page at `/cargo-tracker/mobile.xhtml`. The real Operator and Administrator dashboard links reach that page. Reader receives HTTP 403 on direct access, and anonymous access is redirected to the configured login page. Denied responses contain no protected form payload.

The browser verified that cargo, event type, location, completion time, and voyage controls are present in the same form. An invalid calendar value and a missing voyage for an event that requires one are rejected. The user can leave the page through the cargo list, and saved cargo state remains unchanged. Operator and Administrator flows are evaluated separately for access and role identity.

The group covers legacy callback IDs ACTION-35, ACTION-40, and ACTION-43. Four actor cases passed on a fresh fixture. The fixture passed 661 native checks and 703 browser checks. Current coverage moved from 400 PASS / 70 BLOCKED to 404 PASS / 66 BLOCKED. Historical audit remains 324 PASS / 178 BLOCKED. All 76 retirement cases remain BLOCKED. The fixture removed its owned application/browser containers, private files, and network with no cleanup errors.

The runner fingerprints on-disk inputs and constructed contracts but does not attest the identity of already-imported Python code. Detailed runtime snapshots and raw browser output remain private under `.work/`; committed evidence retains the outcome counts and proof booleans. An earlier browser attempt timed out at 300 seconds after all native checks passed. It was cleaned up and preserved separately. One fresh run after reviewer-approved timeout hardening completed within the 420-second bound.

See [sanitized validation](../../notes/evidence/kan-15-handling-single-page/validation.json).
