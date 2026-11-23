# KAN-23 approved replay and equal-time policy review

Date: 2026-11-23
Task/source revision: KAN-23; starting `main` revision `84822716fc5b949e47304c927f07dc2908b48660`.
Author: primary agent `/root`.
Independent reviewer: `/root/review_kan23_policy` (fresh-context, read-only).

## Scope reviewed

- `candidate/cargotracker/src/main/java/net/java/cargotracker/domain/model/handling/HandlingEvent.java` — SHA-256 `9d9c1b8eace1610eebf09961bdf25f45cebbd04295e673c888359025f0fd5f2b`
- `candidate/cargotracker/src/main/java/net/java/cargotracker/domain/model/handling/HandlingHistory.java` — SHA-256 `b4f5218e03aeabe1b21d87423b7de709351ae51732dcaa095a701140209b975d`
- `candidate/cargotracker/src/test/java/net/java/cargotracker/domain/model/handling/HandlingHistoryTest.java` — SHA-256 `decf7c15564934baa7b89ef95dcc785cafd460fb965d776572a691ebb08c9a19`
- `tests/candidate-runtime/run_candidate.py` — SHA-256 `276ab388a2e1db0ea1a5e121ff3363345520b3641903004b4291618bccf1a6dc`
- `notes/evidence/kan23-policy-decisions/README.md` — SHA-256 `c8c689009e549773fd882cca76bd620cb2c8da1b3978e283c7c6beef995bbad5`
- `notes/evidence/kan23-policy-decisions/focused-test.log` — SHA-256 `6ac1bc89ab85ab937faebb89669bd6aabe07a76b4e7d10166635218f2597b1cc`
- `notes/ai-task-log.md` — SHA-256 `9abb2a0e5842fe70e0a5ba1296cbd31e70e5358d114b0d7c6bcf6a401e071b97`

The user approved request-ID-based replay semantics and ordering equal completion dates by registration date then persisted event ID. The reviewer checked the comparator, JPA DATE precision, equality/dedup semantics, test assertion, runtime count guard, evidence claims and final focused Maven log.

## Verification inspected

Pinned Maven/Temurin 25 image `maven@sha256:9d329e21adce7c0cc53f2fd21e73c127a247c73287b8503196136ec5cff52328`; `HandlingHistoryTest` passed **4 tests**, zero failures, errors or skips; Maven `BUILD SUCCESS`. Captured output: `notes/evidence/kan23-policy-decisions/focused-test.log`. The full disposable runtime suite was not rerun. Existing runtime regression cases already check concurrent same-key/same-payload enqueue-once and same-key/changed-payload rejection. The prior generated-ID replay observation and absence of a dedicated explicit-distinct-client-key live probe are disclosed in the evidence note.

## Findings and verdict

No blocking findings. The reviewer confirmed registration-date then ID ordering is correct for persisted history and that the test, date precision, count guard and evidence agree. Limits are explicitly recorded: unsaved events tied on both dates have null IDs and retain input order; existing `HandlingEvent.equals` deduplicates equivalent events before sorting, even if persisted IDs differ.

Verdict: **APPROVED**. The reviewer re-read the updated evidence note and the captured focused Maven log and confirmed approval remained.
