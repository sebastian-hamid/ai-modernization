# Notification worker and producer boundary

## Functional behavior

WildFly message-driven consumers handle DeliveredCargoQueue, MisdirectedCargoQueue, and RejectedRegistrationAttemptsQueue. They execute under the dedicated notification-worker principal mapped to NotificationWorker. Their EJBs do not expose caller-facing views. Audit events contain fixed event names, consumer kinds, and verified worker identity; they omit cargo identifiers and message bodies.

Application code publishes handling attempts through the HandlingEventRegistrationAttemptProducer EJB. The EJB requires Operator, Administrator, or BatchWorker, then runs as handling-attempt-producer with the single HandlingAttemptProducer broker role. That broker role can send only to HandlingEventRegistrationAttemptQueue. It cannot send to the rejection or delivered notification queues. Human users can authenticate to the remote WildFly naming/JMS endpoint but cannot send to the handling-attempt queue; anonymous connections cannot send either.

Invalid HandlingEventRegistrationAttemptQueue messages receive three total deliveries (the initial delivery plus two retries) with a 250 ms redelivery delay. The candidate sets a 30-second message TTL so the retry window can complete before expiry. Artemis dead-letters exhausted messages to RejectedRegistrationAttemptsQueue; the notification worker records one generic audit event and acknowledges the rejection. A second failure at that queue follows its address setting to the generic DLQ, avoiding a loop.

## Verified in the disposable WildFly fixture

The fresh fixture run on 9 November 2026 passed all 722 checks. A separate JVM connected through WildFly remote+http JMS and verified:

- anonymous send denied;
- Reader, Operator, and Administrator each authenticated successfully and were denied send permission;
- handling-attempt-producer sent one invalid attempt to the handling queue;
- the trusted producer was denied send access to RejectedRegistrationAttemptsQueue and DeliveredCargoQueue;
- denied attempts left business tables unchanged, while the one authorized attempt followed the expected flow.

The broker redelivered that attempt exactly three times, then dead-lettered it once. The rejection consumer acknowledged it, emitted one sanitized audit entry, and left business tables unchanged. The capability gate recorded producer_boundary_verified, trusted_broker_dead_letter_verified, and final_disposition_verified as true. The security unit suite also passed: 88 tests.

Run evidence is in .work/kan18/results.json (local generated fixture output; not committed). This is candidate-runtime evidence only. It does not establish production credentials, TLS policy, firewall rules, secret rotation, or deployment-specific broker configuration.

## Limits and remaining blocks

The fixture configures queue-level least privilege for the candidate runtime. Production deployment must create and rotate a dedicated producer credential, map it to only the handling-attempt send role, protect the remote connector with the intended TLS/network controls, and verify the same policy in its deployment environment. This result does not represent a production deployment or a completed migration of the legacy application.
