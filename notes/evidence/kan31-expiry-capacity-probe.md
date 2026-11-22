# KAN-31 expiry-capacity probe

Date: 2026-11-22

## Scope

Disposable, isolated WildFly/Artemis candidate only. The run used a test-only 5-second handling-attempt TTL and a 1-byte `FAIL` limit on `ExpiryQueue`. The disposable candidate was restarted directly so the non-repeatable bootstrap CLI did not run again. Shared Jenkins and KAN-18 services were not touched.

## Observations

- The first expired test message was present in `ExpiryQueue` before the limit was reached.
- With `ExpiryQueue` full, the next message remained on `HandlingEventRegistrationAttemptQueue` (`MessageCount=1`, expired-counter delta 0); the existing quarantine message remained (`MessageCount=1`, added-counter delta 0). `RejectedRegistrationAttemptsQueue` remained empty.
- After a direct WildFly restart with the capacity limit still set, the source message remained (`MessageCount=1`, expired counter 0) and the original quarantine entry remained (`MessageCount=1`). This verifies persistence across this isolated restart.
- After removing the test limit and restoring `PAGE`, no transfer was observed during a 45-second polling window: source remained at 1 and `ExpiryQueue` remained at 1.
- Artemis logged `AMQ224039` / `ActiveMQAddressFullException` when the first transfer attempt encountered the full expiry address.
- Container, candidate image, and disposable credential files were removed after the run.

## Result and limitation

The probe demonstrates that this broker setup preserves the existing quarantine entry and the incoming expired message while full, including across a server restart. It does **not** demonstrate the approved automatic retry after capacity becomes available. Automatic retry remains an open blocker; do not report the approved full-capacity policy as implemented. Investigate an explicit retry mechanism and test transfer after space is freed before closing this part of KAN-31.

The test uses an artificial one-byte address limit and a 45-second observation window; it does not validate production 1 GiB accounting, alerting, retention, or operator review/replay.

## Follow-up with Artemis `BLOCK`

A separate disposable run changed the one-byte test address policy to Artemis `BLOCK`. The second expired message moved into `ExpiryQueue` despite the test address already containing an entry: source count was 0 and expiry count increased from 1 to 2. This does not enforce the approved strict capacity limit. The result does not justify using `BLOCK` as the 1 GiB quarantine guard.
