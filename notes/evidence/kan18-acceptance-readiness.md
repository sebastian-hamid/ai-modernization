# KAN-18 acceptance readiness

Date: 27 November 2026
Jira: KAN-18 — Modernize the application platform and dependencies
Current status: In Progress
Recommendation: The technical acceptance evidence appears complete; move the issue to In Review for the owner's final acceptance. Do not mark Done until that review is accepted.

## Jira acceptance criteria

> Migrate candidate source/build to the agreed Java/Jakarta/WildFly target; preserve domain behavior and port security controls.
>
> Fresh candidate build/deployment passes intended functional and security suites; dependencies and compatibility changes pinned/documented.

## Evidence map

| Criterion | Evidence | Result |
| --- | --- | --- |
| Agreed target and reproducible build | [Candidate technical README](../../candidate/cargotracker/README.md), [candidate Maven project](../../candidate/cargotracker/pom.xml), [setup status](../setup-status.md), and [Jenkins build 11 evidence](kan18-candidate-scm-build-11/README.md). The candidate is pinned to Java 25 / Jakarta EE 11 / WildFly 42; build 11 used Temurin 25.0.5.1+2 and Maven 3.10.0. | Jenkins SCM build #11 on e153fe2873e3c68eb5215c62e8b14780487ac63c passed and archived the WAR and security JAR. |
| Functional and security behavior | [Patched-JDK integrated runtime and Chromium run](kan18-patchedjdk-browser-20261125/README.md), [KAN-18/KAN-23 runtime regression](kan18-kan23-history-regression/README.md), and the [security suite results](setup-status.md). | Fresh disposable candidate gate: 808/808; Java domain/characterization: 64/64; Flyway V6; Chromium: 970/970. The separate security unit suite passed 145/145. Build #11 additionally passed 132 Python setup/security/harness checks and 64 Maven tests. All reported failures/errors/skips were zero; cleanup was clean. One inherited empty Itinerary TODO is explicitly retained. |
| Database and migration behavior | [Generated-sample migration rehearsal](kan-18-legacy-data-migration-rehearsal.md). | All seven generated sample tables matched field by field after documented timestamp/boolean formatting normalization; 18 foreign keys validated; zero orphan/mismatch checks; Flyway V1–V6. The user confirmed that no retained legacy dataset exists, so retained-data profiling/import is not applicable to current scope. |
| Dependencies, compatibility and documentation | [Candidate technical README](../../candidate/cargotracker/README.md), [candidate documentation index](../../docs/candidate), [setup status](../setup-status.md), and [task log](../ai-task-log.md). | Target versions and compatibility changes are pinned/documented. Historical source and synced references remain read-only. |

The integrated runtime regression started from 4d7ad6e with the reviewed Java/toolchain patch staged in the workspace; that patch was published as 185fdf6. A repository comparison from 185fdf6 to the build-11 revision e153fe2 shows no candidate application source, Maven project, deployment descriptor or database migration changes. Later changes in that range are CI/test plumbing and evidence. This links the fresh runtime regression to the latest packaged candidate while keeping the Jenkins run's narrower scope explicit.

## Independent review

- [KAN-18 regression evidence review](../agent-reviews/2026-11-23-kan18-regression-evidence-review.md)
- [25 November CI portability implementation review](../agent-reviews/2026-11-25-kan18-clean-checkout-ci-followup-review.md)
- [Jenkins build 11 evidence review](../agent-reviews/2026-11-25-kan18-jenkins-build11-evidence-review.md)
- [Overall acceptance-readiness review](../agent-reviews/2026-11-27-kan18-acceptance-readiness-review.md)

The separate reviewer concluded that the evidence supports moving KAN-18 to In Review for owner acceptance, with no material gap blocking that handoff. Corrections requested by that review are recorded in the review record. The Jira owner still makes the acceptance decision.

## Limits and separate work

- The deployment evidence is local and disposable; no production deployment is claimed or required by this ticket. No formal Jakarta EE 11 TCK was run.
- No retained user dataset exists. The generated-sample rehearsal is compatibility evidence, not a claim about arbitrary or production data.
- The inherited empty Itinerary TODO is still not behavioral coverage.
- KAN-14 and KAN-23 remain separate Jira reviews; this summary does not close them.

## Review request

The evidence supports moving KAN-18 to In Review. The issue is ready for In Review and owner acceptance. Do not mark Done until the owner accepts the stated scope and disclosed limits; otherwise, record the specific remaining acceptance gap and keep the ticket open.
