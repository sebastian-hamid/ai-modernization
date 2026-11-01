# AI modernization lab: work completed

Recorded 27 October 2026. Brief factual record for later conversion into step-by-step AI agent instructions. This describes completed work, not a complete modernization procedure. Verification results below are from the recorded runs, most recently Jenkins build 4 on 26 October; services were not all reverified for this document.

## Purpose and boundaries

Established a reproducible legacy Java baseline before changing application behavior. The working repository is `/home/yasinrdp/projects/ai-modernization` in WSL Ubuntu. Preserved the original application checkout, existing Jenkins configuration and credentials, and shared demonstration data. Synced ChatGPT project `sources/` files remain read-only.

## Completed work, in sequence

1. **Verified and repaired the development environment.** Checked WSL2 Ubuntu, Java 21, JAVA_HOME, Maven, Git/GitHub access, Docker and local Jenkins. Installed Ubuntu Maven and made JAVA_HOME consistent across login and interactive shells. Kept Java 21 for modern tooling and isolated the legacy Java 8 toolchain.
2. **Organized the repository and evidence.** Added ignore rules, setup notes, reproduction scripts and provenance records. Reviewed and versioned the setup locally as `baseline-v0.1.0`. GitHub publication of these local changes and SCM-driven CI remain pending; the newer expanded test changes are still uncommitted.
3. **Recovered the legacy build.** Pinned Cargo Tracker to commit `57fc7b32d2597e43b5e0d454e707e0146de5258a`. Recovered historical Eclipse dependencies from their publisher and rebuilt the missing PrimeFaces theme/plugin from pinned official source. Packaged the unchanged application using a pinned Java 8/Maven image. Recorded origins and hashes; did not claim reconstructed artifacts were identical to historical published binaries.
4. **Established the original test baseline.** Enabled tests through a separate test POM because the original build skipped them. Verified 24 reported domain cases; identified one empty TODO and additional unfinished legacy test classes instead of treating them as meaningful coverage.
5. **Recovered the application runtime.** Recorded stock GlassFish 4.1 deployment failure and applied the documented HK2-277 manifest-only correction. Ran the application with embedded Derby/JMS on localhost port 8081. Verified four booking integration tests plus HTTP tracking, routing and asynchronous handling checks.
6. **Automated the baseline in Jenkins.** Preserved controller authentication and storage. Configured a separate non-root build agent, zero controller executors, no agent Docker socket and a local source snapshot with input hashes. Added pipeline stages for tooling checks, source/dependency recovery, packaging, domain tests and runtime checks; archived results and provenance.
7. **Reviewed and captured reusable lessons.** Checked setup scripts and safeguards, verified them in Jenkins, and created the `legacy-java-baseline` skill. Its reusable guidance is separate from repository-specific versions, paths and current status. See [skill notes](skills.md).
8. **Expanded behavior characterization.** Added 10 Java factory cases, 15 live handling workflow cases and two report-generation regression checks. Covered the complete handling journey, malformed inputs, asynchronous failures, lenient dates and off-route events. Added these checks to Jenkins without modifying application production source.

## Latest recorded outcome

Jenkins build 4 succeeded in 114.001 seconds: **53 application cases** (34 domain, four booking, 15 live workflow), with zero failures/errors/skips, plus **10 tooling checks**. One of the original domain cases is still an empty TODO. HTTP smoke assertions are additional checks outside this count.

The tests captured existing defects rather than fixing them: some invalid inputs return HTTP 500, some HTTP 204 requests fail during background processing, invalid calendar dates are accepted, and loading after claim is allowed. A disposable runtime restart also exposed an unresolved deployment/persisted-state failure; an attempted startup change was reverted. The shared demo was preserved.

## Lessons to carry into future agent instructions

- Inspect and preserve existing work before making changes; keep reference material read-only.
- Pin source/toolchains, isolate legacy execution, and retain dependency provenance.
- Separate unchanged application packaging from test-only overlays and runtime compatibility corrections.
- Confirm tests actually execute; distinguish meaningful assertions, empty tests and unfinished suites.
- Verify asynchronous state changes or fresh failure evidence; HTTP acceptance alone is insufficient. Bounded unchanged-state checks do not prove final JMS retry/dead-letter disposition.
- Use disposable seeded runtimes for mutating tests. Account for historical sample dates, date precision and random route output.
- Record failed experiments, exact corrections, evidence and remaining uncertainty. Verify a coherent change in CI before treating it as complete.
- Keep credentials out of instructions and evidence; keep project-specific facts separate from general agent guidance.

## Work still ahead

Define the project objective and acceptance measures; document the current architecture and risks; choose the target architecture and migration sequence; then modernize incrementally and compare against the baseline. Deployment/rollback, security/performance validation and measurement of AI assistance still need to be planned. The legacy baseline is established; the application itself has not yet been modernized.

Near-term follow-ups include reviewing/committing the expanded tests, Jenkins interactive login verification, GitHub publication and SCM integration, disposable runtime restart recovery, and prioritizing remaining browser/CSV/randomness/JMS coverage.

## Supporting records

- [Setup status](setup-status.md)
- [Legacy build recovery](legacy-baseline.md)
- [Runtime recovery](legacy-runtime.md)
- [Jenkins setup](jenkins-baseline.md)
- [Expanded characterization and limitations](handling-characterization.md)
- [Latest Jenkins result](evidence/jenkins-build-4/summary.json)

## Subsequent coverage review (27 October 2026)
Added 81 entrypoint contracts and verified Jenkins build 6 (134 application cases plus 10 tooling checks). Separately confirmed that the access-control requirement fails: anonymous operational reads/writes and cross-origin WebSocket handshakes are allowed. Documented remaining browser, identity/role, malformed-input, batch, concurrency and resilience gaps in [test-coverage-review.md](test-coverage-review.md). Application production source remains unchanged.

## Baseline documentation (28 October 2026)
Created source/evidence-checked functional, architecture and technical documentation under [docs/baseline](../docs/baseline/README.md), with commit-specific source references and a SHA-256 verification manifest. Clarified destructive startup initialization, two-minute batch scheduling, one-second attempt TTL and unverified rejection/dead-letter behavior. No application changes, service restarts or new runtime tests were performed; gaps remain explicitly labeled.

## 1 November 2026 — KAN-14 desired access tests

Defined 502 policy-derived actor/surface/session cases, with fail-closed candidate assertions. Sixteen oracle unit checks pass; these use artificial observations and are not application coverage. A fresh disposable legacy run reports two public-page successes and eight desired-security failures, including anonymous state mutation. Candidate gate explicitly reports all 502 BLOCKED (exit 2) pending real login/session/browser and independent effect observers in KAN-15. Shared services and original sources preserved. Independent review found two oracle false-pass paths; corrected with regression tests. Ticket remains In Review: actual denied-write queue/persistence absence verification awaits KAN-15 candidate security and independent observers. Local files only.

## 1 November 2026 — KAN-15 local identity/session foundation (in progress)

- Implemented reusable container-login, session CSRF/logout, explicit HTTP path roles and CDI method roles under candidate/security. Kept integration test WAR under tests/security-runtime separate from Cargo Tracker.
- Fresh pinned WildFly/Java25 fixture passes 49 runtime checks: actual local accounts/roles, session ID rotation, CSRF, direct service-role denial, logout replay and real server idle expiry. Three cleanup regressions pass (partial secret initialization, Docker log failure and container removal failure). Runtime/private realm files removed; historical source/demo/Jenkins preserved.
- This does not implement full KAN-15 or unblock KAN-14: actual Cargo Tracker candidate bootstrap (overlaps KAN-18), all callbacks/EJB/machine boundaries, WebSocket revocation and real database/queue/business-audit observers remain required. KAN-15 stays In Progress. See candidate/security/README.md; independent review/recheck complete with no remaining material foundation findings after cleanup correction. No commit/push. Human effort/review time/cost unavailable; no savings claim.
