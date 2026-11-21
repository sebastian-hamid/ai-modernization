# KAN-16 confirmed anonymous operational access

Date: 2026-11-17 (Europe/Bratislava)

## Result

The scoped KAN-16 acceptance is verified against the fresh candidate fixture captured for KAN-15 run `kan15-handling-pages-d`:

- Baseline coverage evidence recorded **13 anonymous operational surfaces** and a failing access-control gate. Twelve HTTP read/write findings are in KAN-16 scope; the separate anonymous cross-origin WebSocket handshake remains tracked under KAN-17.
- The ten confirmed direct operational page paths now return the configured login redirect to anonymous users, return 403 to Reader where the approved policy excludes Reader, and return 200 with server-verified identity to the allowed roles.
- Cargo monitoring API-01 returns 401 anonymously and 200 to Reader, Operator, and Administrator.
- Handling report API-02 returns 401 to anonymous, 403 to Reader, and 204 to Operator and Administrator. The authenticated successful writes have verified positive effects.
- Valid denied anonymous/Reader handling reports and missing/wrong-CSRF writes were checked against settled database, queue, and business-invocation snapshots. The complete before/after snapshots are equal: six database tables, seven queues, and 22 business invocation counters.
- The fresh candidate fixture passed 777 checks; the browser fixture passed 970 checks. Fixture-owned containers, files, and network were cleaned up.

At the time of this 17 November scope run, the KAN-15 overall gate exited 2 because four unrelated ACTION-43 retirement rows remained BLOCKED. Later on 17 November, the user approved retiring only the old page hook, and the independently reviewed effective replay became 470 PASS / 76 RETIRED / 0 BLOCKED (exit 0). The preserved historical audit remains separate at 317 PASS / 7 FAIL / 178 BLOCKED. The scoped KAN-16 access evidence remains independently approved and does not depend on the ACTION-43 classification.

## Evidence

- [Validation details and source hashes](validation.json)
- [Baseline coverage review](../../test-coverage-review.md)
- [Baseline strict access-control evidence](../coverage-review-2026-10-27/strict-gate-summary.json)
- [Fresh KAN-15 candidate, browser, and gate results](../kan-15-handling-page-retirement/)

This is a scoped access-control verification from the local synthetic candidate; it is not a production deployment or a claim that the entire 502-case access catalogue is complete. The candidate runner deliberately keeps the global `denied_write_absence_verified` flag false until the full catalogue is complete. KAN-17 WebSocket authorization and origin policy are outside this ticket.


## Jira status update — 21 November 2026

The KAN-15 dependency is now Done. KAN-16's scoped access-control evidence and independent review were already complete; this ticket remains scoped to the 12 HTTP findings and makes no full-catalogue or production claim.
