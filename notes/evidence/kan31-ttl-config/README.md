# KAN-31 handling-attempt TTL configuration evidence

## Scope

This change replaces the hard-coded handling-attempt producer lifetime with the WildFly system property cargo.handling.attempt.ttl.ms. The versioned candidate CLI configures it from CARGO_HANDLING_ATTEMPT_TTL_MS, defaulting to 30,000 milliseconds. The application uses the same default when the property is absent and rejects malformed, zero, or negative values.

## Verification

- Source revision before this change: d21809d (Record KAN-31 full-quarantine retry decision).
- Fresh disposable run ID: kan31-ttl-policy.
- Test override: CARGO_HANDLING_ATTEMPT_TTL_MS=45000.
- WildFly JVM inspection observed cargo.handling.attempt.ttl.ms=45000, matching the configured environment override.
- Candidate domain/characterization tests: 61 passed; 0 failures, errors, or skips.
- Full candidate runtime checks: 796 passed; 0 failed.
- Owned fixture container and private credential files were removed; cleanup errors: none.
- Shared KAN-18 and Jenkins containers remained running. Task-owned build images were removed after evidence capture.

The compact, committed receipt is in [candidate-runtime.json](candidate-runtime.json). The complete per-check receipt remains in the ignored local .work directory; its SHA-256 is recorded in the JSON summary.

## Limits

This proves application configuration propagation and the producer's configuration reader, not message expiry timing under the 45-second override. KAN-25's earlier observation showed a 30-second message expiry in a prior runtime. Seven-day quarantine retention, 1 GiB enforcement, full-capacity pending/retry, alerting, Administrator review/replay, and request-ID idempotency are not implemented or verified by this run.
