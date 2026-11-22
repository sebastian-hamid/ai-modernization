# KAN-18 candidate runtime regression after KAN-31 PostgreSQL quarantine

- **Result:** PASS, run kan18-post-kan31-pg-regression-r20, 22 November 2026.
- **Runtime evidence:** 805 of 805 isolated checks passed. The pinned WildFly candidate ran against PostgreSQL 18.6 with the Flyway V1–V6 schema; 63 candidate domain tests passed (0 failures, 0 errors, 0 skipped).
- **Preserved KAN-18 checks:** candidate runtime authorization/session, page and API behavior, handling flows, and batch import checks completed without regression.
- **Quarantine and business effects:** invalid handling attempts were durably quarantined with no handling/cargo business effects; valid batch import retained its idempotency record and exact intended business effects. The test verified a RECEIVE at CNHKG followed by CLAIM at FIHEL, then verified that LOAD after CLAIM is quarantined, does not add a handling event or alter cargo state, and is visible through the Administrator quarantine API. The LOAD-specific runtime log segment was verified sanitized.
- **Resource cleanup:** the owned candidate container, PostgreSQL Compose resources, host-access network, disposable image and private generated files were removed. No cleanup errors were reported. Shared KAN-18 and Jenkins services were preserved.
- **Scope:** this run validates the candidate runtime and the listed regression paths. It is not, by itself, evidence that every KAN-18 acceptance item or the full modernization is complete.
- **Reproduction:** from the WSL Ubuntu repository root, use a new run ID whose .work directory does not already exist (for example, r21): AI_MODERNIZATION_LIVE_RUN_ID=kan18-post-kan31-pg-regression-r21 python3 tests/candidate-runtime/run_candidate.py.
- **Raw receipt:** .work/kan18-post-kan31-pg-regression-r20/candidate-runtime/results.json is local ignored run material and is not committed. This note contains only the concise result and no credentials or raw runtime logs.




