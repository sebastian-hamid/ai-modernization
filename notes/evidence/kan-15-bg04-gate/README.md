# KAN-15 BG-04 - Cargo inspection worker boundary

## Scope

BG-04 covers `CargoHandledQueue -> CargoHandledConsumer -> inspectCargo -> CargoInspected`. The candidate now assigns a dedicated `InspectionWorker` run-as identity, restricts `DefaultCargoInspectionService` to that role, and writes a server-side audit record that checks the actual principal/role and validates a server-generated correlation UUID plus the producer-origin property.

## Fresh validation

Run from the repository root:

```sh
python3 tests/security/run_current_capabilities.py --live-subset --output notes/evidence/kan-15-bg04-gate/validation.json
```

The completed fresh run used fingerprint `2f92b4a3006d11c18f178c76a45ecf3f9a770b9c33ff0747dc48cd3ed68372c8`. The pinned WildFly 42/Java 25 candidate passed 710 native checks and 841 Chromium checks. The runtime report is `.work/kan18/results.json`; the sanitized current-capability gate and provenance are in `validation.json`.

All four human BG-04 direct-service cases passed:

- Anonymous: 401, no protected payload or independently observed effects.
- Reader, Operator, Administrator: 403 at the EJB boundary, no protected payload or effects.

BG-04-MACHINE remains BLOCKED. The fixture observed the worker principal `inspection-worker`, role `InspectionWorker`, three unique correlation UUIDs, and matched queue additions/acknowledgements, consumer invocations and audit entries. However, it does not test restrictions on arbitrary JMS/JNDI producers. The report explicitly sets `producer_boundary_verified=false`; no producer trust claim is made.

The gate reports 440 PASS / 30 BLOCKED for current capabilities, 76 retirement cases BLOCKED, and historical audit 324 PASS / 178 BLOCKED. Exit 2 is expected while blockers remain. Retired entries are not counted as PASS.

## Fixture and test configuration

The disposable WildFly fixture sets the metrics subsystem `exposed-subsystems=[]`. WildFly's metrics collector otherwise attempted to read Jakarta Batch execution metrics as anonymous and failed with `BatchPermission read`. Disabling subsystem-metric exposure only in the disposable fixture avoids that unrelated registration failure while preserving the restrictive BatchPermission policy. The candidate's production configuration and permissions were not broadened.

A completed fixture attempt first failed the exact invocation-delta assertion because the new `InspectionWorkerAudit#recordConsumedAttempt` call was not yet included in the expected delta. The assertion was corrected to require exactly one such invocation; the subsequent fresh run passed. An earlier interrupted diagnostic run produced no acceptance evidence; its owned container and private credentials were cleaned before the completed run.

Focused suites passed: security 87, candidate-runtime 42, browser-workflow 30. `git diff --check` is clean. Runtime cleanup succeeded: candidate/browser containers, private browser network and generated credentials removed without cleanup errors.

## Limits

The producer-origin string and correlation UUID are message metadata, not authenticated producer identity. Arbitrary broker producers, external JNDI access, broker ACLs, and crash/replay deduplication were not verified. Therefore the machine case remains blocked. No production deployment occurred; synced `sources/` remained read-only. KAN-15 remains in progress pending producer-boundary evidence.
