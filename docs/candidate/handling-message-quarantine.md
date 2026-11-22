# Handling-message quarantine

## Approved policy

- Handling-attempt messages use a configurable 30-second producer TTL.
- Expired or exhausted messages are quarantined for review and explicit, controlled manual replay. Automatic replay is not allowed.
- Quarantine retention is at most 7 days; unreviewed entries are then disposed.
- Quarantine capacity is 1 GiB. At capacity, stop accepting new quarantine entries, alert the operator, and preserve existing entries for their approved retention window.
- An incoming expired message that cannot enter a full quarantine remains durably pending and is transferred when space becomes available.
- Only users in the existing Administrator role may inspect or manually replay quarantined messages.
- Request-ID behavior: same ID and same payload is accepted once; same ID with a changed payload is rejected; different IDs identify distinct submissions, even if the event fields match. This does not promise exactly-once business effects.

## Implemented and verified

The candidate handling-attempt producer now reads cargo.handling.attempt.ttl.ms, with a 30,000 ms default. The versioned WildFly messaging CLI maps CARGO_HANDLING_ATTEMPT_TTL_MS to that system property. In fresh disposable run kan31-ttl-policy, WildFly reported the 45,000 ms override. The Java 25 candidate build passed 61 domain/characterization tests, and the full candidate runtime passed 796 checks. See [KAN-31 TTL evidence](../../notes/evidence/kan31-ttl-config/README.md).

## Not yet implemented or verified

The KAN-25 observation established that one expired message reached WildFly's default ExpiryQueue; it did not establish bounded quarantine. The following parts of the approved policy still require an implementation and fresh isolated proof:

- A durable quarantine with 7-day disposal and a configurable retention setting.
- A 1 GiB broker-accounted capacity limit with a configurable cap and clear size metric.
- At-capacity alerting and strict bounded quarantine behavior. A disposable KAN-31 probe confirmed that `FAIL` preserves the original quarantine entry and leaves the incoming expired message on its source queue, including across restart, but that message did not transfer after capacity was freed during a 45-second observation. Artemis `BLOCK` allowed the second test message into the one-byte-limited quarantine, so it is not a proven strict-capacity solution. See [expiry-capacity probe evidence](../../notes/evidence/kan31-expiry-capacity-probe.md).
- Administrator-only review, explicit audited manual replay, and direct-API denial for every other role.
- Durable request-ID idempotency under concurrent same-ID submissions, changed-payload rejection, and distinct-ID behavior.

Do not infer successful message-expiry timing from the 45-second JVM-property check. The runtime evidence only verifies the override reaches WildFly and the configuration-reader tests validate the application setting.
