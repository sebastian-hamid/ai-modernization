# Handling-message quarantine

## Functional policy

Handling attempts have a configurable 30-second producer time-to-live. Expired attempts and attempts that exhaust the application handler's retry limit are routed to a durable intake queue, then stored in PostgreSQL for operator review. There is no automatic replay.

Quarantine payload retention defaults to seven days and may be shortened through configuration; the configured value cannot exceed seven days. Expired payload rows are deleted by a scheduled job. Replay audit records and request-idempotency records outlive payload retention.

The configured capacity defaults to 1 GiB. Capacity counts the UTF-8 bytes of a canonical representation of each stored handling attempt (tracking ID, event type, UN/LOCODE, voyage number, registration timestamp and completion timestamp), not PostgreSQL row size or broker/disk usage. When an attempt cannot fit, the consumer transaction rolls back, the durable intake message remains pending for retry, and the system records/logs an operator alert. Existing quarantine rows remain available until their retention expires. When retention frees capacity, pending intake retries; the alert stays active until every message blocked by capacity has transferred.

Only the existing `Administrator` role may inspect quarantine status and payloads or request manual replay. Anonymous users and `Reader`, `Operator` and handling service roles are denied by both route and application authorization. A successful replay request queues the event, removes the active quarantine payload and writes an audit record; HTTP acceptance does not prove the business handler completed successfully. Replaying an item already queued or processed is rejected. If the replay later expires or exhausts retries, it can be quarantined again under the same request ID.

For `Idempotency-Key`, the same key and same payload enqueue once, while the same key with a changed payload returns HTTP 409. Different keys represent separate submissions even when event fields match. Requests without a key retain backward-compatible behavior through a generated UUID; callers that may retry should supply a stable key. This is not a global exactly-once guarantee.

## Administrator API

- `GET /cargo-tracker/rest/handling/quarantine` returns configured capacity and retention, logical bytes in use, alert state and unexpired entries.
- `POST /cargo-tracker/rest/handling/quarantine/replay?id={entryId}` queues one explicit replay and records the authenticated administrator and request ID. The existing authenticated session and CSRF protection apply.

An administrator should review the event and its downstream effects before replaying it. The API prevents duplicate replay submission while the request identity is queued or already processed.

## Verified implementation

The producer attaches a distinct stable key to each broker message so the pending-capacity ledger survives expiry/dead-letter routing and redelivery. The isolated PostgreSQL/WildFly verifier has exercised expiry and retry-exhaustion routing; durable pending delivery at capacity; persistence across disposable candidate-container replacement; transfer after capacity is freed; retention-driven recovery of a pending message and alert; same-key concurrency and payload-conflict behavior; distinct request IDs; Administrator-only review and replay; replay audit; and payload cleanup with audit retention. Evidence is in [KAN-31 runtime verification](../../notes/evidence/kan31-postgres-quarantine/README.md).

The latest fresh characterization suite reported 63 tests with no failures, errors, or skips (run `kan31q-da9cd525`; see the evidence record). The runtime probe uses a 100-byte cap and 600-second retention override for bounded execution; a characterization test verifies the defaults of 1,073,741,824 bytes and 604,800 seconds. This verifies configuration behavior, not long-duration expiry at the seven-day default.