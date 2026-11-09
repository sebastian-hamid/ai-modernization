# Notification worker boundary

## Functional behavior

WildFly message-driven consumers handle `DeliveredCargoQueue`, `MisdirectedCargoQueue`, and `RejectedRegistrationAttemptsQueue`. They execute under the dedicated `notification-worker` principal mapped to `NotificationWorker`. The consumers do not expose a caller-facing EJB view. Their audit event contains only a fixed event name, consumer kind, and verified worker identity; it excludes cargo identifiers and message bodies.

Invalid `HandlingEventRegistrationAttemptQueue` messages receive three total deliveries (the initial delivery plus two retries) with a 250 ms redelivery delay. The candidate sets a 30-second message TTL so the broker retry window can complete before the message expires; the historical candidate value was 1 second, which was too short for the configured retry schedule. Artemis dead-letters the exhausted message to `RejectedRegistrationAttemptsQueue`. The dedicated consumer records one generic audit event and acknowledges the rejected message. A second failure at the rejection queue follows the broker address setting to the generic `DLQ`, rather than looping.

## Verified in the disposable WildFly fixture

The 8 November 2026 live fixture passed 723 checks. It verified all three MDBs start, human direct-client access to their views is denied for anonymous, Reader, Operator, and Administrator, and unauthorized direct poison-message publishing is denied without effects. For the rejection flow it observed three input-consumer invocations, three handling-worker audit calls, one broker dead-letter delivery, one rejection-consumer invocation, one notification audit, one acknowledged rejection message, empty queues afterward, unchanged application tables, and no tracking ID in server logs. The source message increments Artemis `MessagesKilled` on dead-lettering; the rejection message increments `MessagesAcknowledged` on successful consumption. Sanitized fixture output is recorded in `notes/evidence/kan-15-bg05-gate/candidate-runtime.json`.

## Limits and remaining blocks

The test publishes the invalid message through a fixture-only Administrator endpoint and verifies broker-managed dead-letter routing. It does not prove authorization for arbitrary external JMS/JNDI producers or production broker credentials and network boundaries. BG-05's machine capability therefore remains BLOCKED until those producer boundaries are defined and tested against the intended deployment configuration. The native BG-05 observer's queue-cycle counters cover the rejected-registration message. In the same fresh full gate, the browser workflow also produced one delivered and three misdirected worker audit records. The audit logs establish that those callbacks executed; this checkpoint does not retain separate before/after queue-counter receipts for those browser-generated messages.

This is candidate runtime evidence, not a production deployment or a claim that the legacy application has been migrated.
