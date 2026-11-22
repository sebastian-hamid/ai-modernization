# KAN-31 TTL configuration review

- Task: KAN-31 configurable handling-attempt TTL implementation slice.
- Reviewed working tree: based on d21809d (Record KAN-31 full-quarantine retry decision).
- Reviewer: /root/review_kan31_ttl_config (separate read-only agent).
- Review date: 22 November 2026.
- Inputs: WildFly messaging CLI, handling-attempt producer and configuration reader, characterization tests, disposable runtime runner and harness tests, policy documentation, setup status, task log, and saved KAN-31 runtime receipt.
- Checks: Reviewed TTL property mapping/default, numeric validation behavior, restoration of global system property in tests, runtime property assertion, unique KAN-31 fixture namespace, cleanup behavior and saved evidence. Reviewer ran no services and made no edits.
- Author verification inspected: Pinned Java 25 Docker build passed 61 domain/characterization tests; the fresh isolated KAN-31 runtime passed 796 checks with environment override 45000 ms and live JVM readback 45000 ms; Python disposable-harness tests passed 11 tests; cleanup removed the fixture container/private credentials and task-owned images with no cleanup errors; shared KAN-18 and Jenkins remained running.
- Findings: No remaining material findings.
- Limitation: An invalid TTL property fails when the producer reads it, not proactively at application startup. It does not fall back silently.
- Verdict: Reviewed and approved with no remaining material findings.
- Remaining KAN-31 scope: bounded quarantine retention/capacity, full-capacity pending/retry and alert, Administrator-only review/manual replay, and request-ID idempotency remain unimplemented and unverified.

## Compact evidence follow-up

A read-only reviewer follow-up verified the compact candidate-runtime.json summary and SHA-256 against the full ignored .work receipt. It confirmed 796/796 checks, 61 domain tests, 45,000-ms property readback, image ID and cleanup fields. No material findings; no files were edited and no services were run.
