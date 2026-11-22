# KAN-18 Chromium regression after KAN-31 PostgreSQL quarantine

- **Result:** PASS, run `kan15-kan18-post-kan31-browser-r3`, 23 November 2026.
- **Candidate runtime:** 808 of 808 isolated checks passed against disposable PostgreSQL 18.6 and the Flyway V1-V6 schema. This included candidate application, handling, authorization, database, queue, business-effect, and cleanup assertions.
- **Browser workflows:** 970 of 970 real Chromium checks passed across cargo read, booking, destination change, routing, live tracking, handling, notification, session revocation, and callback retirement workflows. There were no browser resource errors.
- **Quarantine regression:** the run verified the current KAN-31 PostgreSQL quarantine paths in the integrated browser-backed candidate, including invalid attempts, retention/intake, and Administrator access. Browser workflow results and candidate-runtime evidence are separate receipts; the 970 browser checks are not database checks.
- **Resource cleanup:** the owned candidate and Chromium containers, PostgreSQL Compose resources, host-access network, disposable images, and private generated files were removed. No cleanup errors were reported. Shared KAN-18 and Jenkins services were preserved.
- **Scope:** this run verifies the integrated candidate and the browser paths covered by this suite. It does not complete all KAN-18 acceptance criteria or resolve the separate stale historical security/review-receipt gates.
- **Reproduction:** from the WSL Ubuntu repository root, use a new unused run ID: `AI_MODERNIZATION_LIVE_RUN_ID=kan15-kan18-post-kan31-browser-r4 python3 tests/browser-workflows/run_browser.py`.
- **Raw receipts:** `.work/kan15-kan18-post-kan31-browser-r3/browser/results.json` and `.work/kan15-kan18-post-kan31-browser-r3/candidate-runtime/results.json` are ignored local run material and are not committed. This note records the concise result without credentials or raw runtime logs.
