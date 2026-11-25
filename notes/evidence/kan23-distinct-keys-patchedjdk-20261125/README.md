# KAN-23 explicit idempotency-key behavior on patched Java

Date: 25 November 2026
Runtime run: kan31q-97100af9
Source revision: 185fdf6, with a test-evidence detail-only change in the disposable verifier.

A fresh no-cache candidate build used Temurin 25.0.5.1+2 and Maven 3.10.0. All 64 domain/characterization tests passed, Flyway reached V6, and the disposable quarantine runtime passed 46/46 checks.

The focused KAN-23 check submitted two identical LOAD report payloads for the same synthetic tracking ID with two different explicit Idempotency-Key values. Both requests returned HTTP 204. With the registration queue paused, the queue gained exactly two messages and the idempotency ledger gained exactly two rows. Before/after queue and ledger observations are included in [summary.json](summary.json).

Cleanup removed the disposable Compose resources, image and private credentials. Jenkins and the shared KAN-18 runtime were left running. The ignored raw receipt is SHA-256 pinned in the summary and was not committed.

This proves acceptance and separate durable queue/idempotency entries for distinct explicit request IDs. The queue was intentionally paused during this assertion, so this evidence does not claim downstream processing of both messages. The separate earlier no-key duplicate event probe is recorded in notes/evidence/kan23-duplicate-handling-event/.

Independent evidence review found no material findings: [review record](../../agent-reviews/2026-11-25-kan23-distinct-keys-review.md).
