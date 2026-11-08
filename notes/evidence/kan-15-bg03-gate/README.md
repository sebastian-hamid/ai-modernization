# KAN-15 BG-03 - Handling event worker boundary

## Scope

BG-03 verifies that application users cannot directly invoke the handling-event service and that authorized Operator and Administrator submissions are processed by a dedicated HandlingWorker identity. The fixture verifies the actual WildFly principal and role through a server-side audit bean.

## Fresh validation

Command from the repository root:

    python3 tests/security/run_current_capabilities.py --live-subset --output notes/evidence/kan-15-bg03-gate/validation.json

The final frozen-source run compiled the candidate in the pinned Java 25 WildFly image and passed 705 native checks plus 841 Chromium checks. Candidate/browser containers and the private browser network were removed. Private fixture credentials were removed and cleanup recorded no errors.

The four human BG-03 cases passed:

- Anonymous direct service access: 401; no protected payload or effects.
- Reader, Operator, and Administrator direct service access: 403 at the EJB authorization boundary; no protected payload or effects.

BG-03-MACHINE remains BLOCKED. The fixture verified the consumed-message principal handling-worker and role HandlingWorker after authorized application submissions, but it did not verify that arbitrary JMS/JNDI producers are denied. The approved inventory includes that producer boundary in BG-03's control, so consumer identity evidence alone cannot satisfy the machine case. The run explicitly records producer_boundary_verified=false.

The current capability gate reports 436 PASS / 34 BLOCKED. The 34 blockers include BG-03-MACHINE and 33 cases without candidate adapters. Historical audit remains 324 PASS / 178 BLOCKED. All 76 retirement candidates remain BLOCKED and do not count as PASS. Gate exit 2 is expected while blockers remain. The full sanitized run and provenance are in validation.json.

## Focused verification

- python3 -m unittest discover -s tests/security -p "test_*.py" -q - 86 passed.
- python3 -m unittest discover -s tests/candidate-runtime -p "test_*.py" -q - 42 passed.
- python3 -m unittest discover -s tests/browser-workflows -p "test_*.py" -q - 30 passed.
- git diff --check - clean.

## Limits

The evidence proves the EJB authorization boundary and the configured local queue consumer identity in the disposable WildFly fixture. It does not prove broker authentication/ACLs for arbitrary producers, external JNDI restrictions, or crash/replay deduplication. The user-facing application role does not automatically become the consumer identity; this run verifies the explicit @RunAs mapping and server-side audit bean.

No production deployment occurred. sources/ remained read-only. KAN-15 remains In Progress pending producer-boundary evidence and other backlog work.
