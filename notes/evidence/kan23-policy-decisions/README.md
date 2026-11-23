# KAN-23 approved replay and event-order policies

Date: 2026-11-23

The user approved these behavior decisions for KAN-23:

- A repeated request with the same `Idempotency-Key` and identical payload is a replay and is suppressed. Reusing that key with a different payload is rejected. Identical payloads submitted with a different key are distinct reports and are accepted; a missing key receives a generated request ID, so a later submission is distinct as well.
- Handling events sort by completion date, then registration date, then persisted event ID. Registration timestamps are stored at date precision, so event ID resolves same-day ties.

The candidate already reserves request IDs uniquely and compares payload identity in `HandlingRequestIdempotencyService`; this change records the approved contract without changing that implementation. Existing disposable-runtime coverage checks concurrent same-ID/same-payload requests enqueue once and same-ID/changed-payload requests return 409 without enqueue (`tests/candidate-runtime/quarantine/verify_quarantine.py`). A prior KAN-23 isolated observation replayed an identical report without a client key; because the endpoint generates request IDs, the second report was stored and processed again. The observation recorded repeated persistence and asynchronous work, so duplicate reports must not be described as having no downstream effects: `notes/evidence/kan23-duplicate-handling-event/README.md`. There is not yet a dedicated live probe for identical bodies with two explicit client-supplied distinct keys.

Equal-time ordering is implemented in `HandlingHistory` and covered by `HandlingHistoryTest.testEqualCompletionTimesAreOrderedByRegistrationThenId`, which assigns IDs to transient test objects. For persisted events, completion date, registration date and ID provide the selected deterministic order. Unsaved events with null IDs tied on both dates retain input order; this contract applies to persisted history. Existing `HandlingEvent.equals` semantics also deduplicate equivalent events before sorting, even when their persisted IDs differ. Focused pinned Java 25 Maven verification passed **4 tests** with zero failures, errors, or skips on 2026-11-23; the captured output is in [focused-test.log](focused-test.log). The full disposable runtime suite was not rerun for this scoped unit change. The candidate runtime's committed test-count guard is raised to 64 so its next full run enforces the added domain test.

The focused Maven attempt used an isolated `.work/kan23-target`, `.work/kan23-security-target`, and `.work/kan23-m2`; only ignored generated artifacts were written there. No live application services or historical sources were changed.
