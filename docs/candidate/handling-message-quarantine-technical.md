# Handling-message quarantine technical guide

## Runtime configuration

The WildFly CLI file `candidate/cargotracker/deployment/wildfly/notification-disposition.cli` maps these environment variables to JVM system properties:

| Environment variable | System property | Default | Constraints |
| --- | --- | ---: | --- |
| `CARGO_HANDLING_ATTEMPT_TTL_MS` | `cargo.handling.attempt.ttl.ms` | `30000` ms | Positive; producer message TTL |
| `CARGO_HANDLING_QUARANTINE_MAX_BYTES` | `cargo.handling.quarantine.max.bytes` | `1073741824` bytes | Positive integer |
| `CARGO_HANDLING_QUARANTINE_RETENTION_SECONDS` | `cargo.handling.quarantine.retention.seconds` | `604800` seconds | Positive and no greater than seven days |
| `CARGO_HANDLING_QUARANTINE_REDELIVERY_DELAY_MS` | `cargo.handling.quarantine.redelivery.delay.ms` | `30000` ms | Positive broker retry delay for pending intake |

Capacity is a logical sum of canonical UTF-8 payload bytes, not a disk quota. Pending broker messages and PostgreSQL indexes/WAL are not included in this byte limit. Database and broker physical storage still need host-level monitoring and operational limits.

## Schema and lifecycle

Flyway migration `V4__handling_attempt_quarantine.sql` adds the quarantine payload, singleton capacity state and replay audit. `V5__handling_request_idempotency_and_replay.sql` adds stable request identity, payload hashes and replay request IDs, while retaining audit records when payloads expire. `V6__track_pending_quarantine_intake.sql` records each broker message blocked by capacity until its payload commits. The asynchronous capacity callback locks the request identity before the capacity state and records a marker only while the request remains queued; this serializes it with successful quarantine transfer and prevents a late callback from leaving a stale marker. Pending records are keyed by the stable producer message property. For older messages without that property, the broker message ID is used when available; otherwise a deterministic legacy request identity uses the attempt registration time and payload hash so a redelivery resolves the same marker. Distinct old messages with identical payload and identical registration timestamps cannot be distinguished if the broker supplied no message ID; new producers always attach a unique property. Do not edit published migrations; add a new versioned migration for later schema changes.

The scheduled retention job runs every second and deletes payload rows after `expires_at`. API inspection, logical byte accounting and replay eligibility also enforce `expires_at`, so delayed cleanup does not make an expired payload visible or replayable. Retention frees logical capacity; a hashed broker message ID tracks each blocked intake until it transfers, and the alert clears only when all blocked messages have transferred; a successful transfer clears its own marker, and the global alert remains active while any marker remains. Replay audit and idempotency ledger records currently have no cleanup policy and therefore accumulate; decide and implement a separate retention policy before production scale.

## API and operations

- Inspect state: `GET /cargo-tracker/rest/handling/quarantine` (Administrator only).
- Request replay: `POST /cargo-tracker/rest/handling/quarantine/replay?id=<entry-id>` (Administrator only; normal session and CSRF requirements apply).
- Inspect WildFly logs for `HANDLING_QUARANTINE_FULL` and `HANDLING_QUARANTINE_CAPACITY_RECOVERED`.
- At capacity, the intake broker queue retains messages and retries at the configured delay (30 seconds by default). Resolve room by allowing approved retention or another approved cleanup process to free payload capacity; never delete review items manually in production without an approved disposition.
- Replay returns `202 Accepted` when a message has been enqueued and removes that active payload row while retaining the audit. If it later fails or expires, it can re-enter quarantine with the same request ID. The old quarantine entry ID cannot be replayed twice. `202` does not mean downstream processing succeeded; inspect downstream application results separately.

## Disposable verification

Run from the repository root in WSL Ubuntu:

```bash
python3 tests/candidate-runtime/quarantine/verify_quarantine.py
```

The verifier creates a uniquely named Docker Compose project, random temporary credentials, a random localhost port and disposable PostgreSQL/WildFly containers. It overrides capacity to 100 logical bytes and retention to 600 seconds, builds the candidate image freshly, tests the scenarios in the evidence record, then removes the project volumes, image and temporary credentials. It must not target the shared Jenkins or KAN-18 services. Confirm cleanup fields in the generated result before using the run as evidence.

The fresh Maven build runs the Java characterization tests. The runtime probe does not wait seven days; default retention and cap values are covered by Java characterization tests rather than long-term timing.