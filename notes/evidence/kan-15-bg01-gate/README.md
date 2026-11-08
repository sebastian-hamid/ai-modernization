# KAN-15 BG-01 human authorization gate evidence

## Scope

This increment binds the fresh batch-import runtime probes to the current-capability gate for the BG-01 human cases. It covers anonymous, Reader, Operator, and Administrator only. The separate BG-01-MACHINE case remains BLOCKED pending a dedicated machine-scope adapter.

## Verified outcomes

- Anonymous import GET/POST returned configured-login 303 responses, no protected payload, and unchanged database, broker, and business-invocation snapshots.
- Reader and Operator import GET/POST returned 403, direct JobOperator read/start probes were denied, and independent effects remained unchanged.
- Administrator used the authorized current form with CSRF and ViewState, started one controlled import, and the batch ran under the restricted batch-worker identity.
- The valid staged RECEIVE event persisted with expected database, JMS queue, and invocation effects.
- Each denied human request group has fresh before/after snapshots tied to the same owned runtime; direct JobOperator denials have a separate settled effects comparison.

The complete fresh report is [validation.json](validation.json). The worker machine-identity case remains blocked and is not inferred from the Administrator result.

## Validation

- Fresh native runtime checks: 696 passed.
- Fresh Chromium browser checks: 841 passed.
- Current capability gate: 428 PASS / 42 BLOCKED.
- Retirement inventory: 76 BLOCKED. Gate exit 2 reflects remaining work.
- Focused tests: 28 security, 42 candidate-runtime, 30 browser harness; syntax compilation and git diff checks passed.
- Owned app/browser containers, private files, and networks were cleaned up.

The gate records that on-disk input fingerprints are bound, but imported Python code identity is not attested. No production deployment or synced sources/ changes.
