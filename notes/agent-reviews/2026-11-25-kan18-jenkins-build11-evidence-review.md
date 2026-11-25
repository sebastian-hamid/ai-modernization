# Independent evidence review — KAN-18 Jenkins build 11

Date: 25 November 2026
Reviewer: /root/review_kan18_build11_evidence
Verdict: APPROVED; no material discrepancies.

## Scope reviewed

The reviewer checked notes/evidence/kan18-candidate-scm-build-11/README.md, notes/evidence/kan18-candidate-scm-build-11/summary.json, notes/setup-status.md and notes/ai-task-log.md against Jenkins candidate build #11.

## Findings

- Jenkins reports SUCCESS in 64.905 seconds on revision e153fe2873e3c68eb5215c62e8b14780487ac63c; the pipeline enforces that the workspace revision matches the SCM revision.
- Jenkins logs confirm the pinned detached legacy-source fetch at 57fc7b32d2597e43b5e0d454e707e0146de5258a and toolchain versions Temurin 25.0.5.1+2, Maven 3.10.0, Python 3.14.4 and Git 2.53.0.
- Suite totals match the logs: 132 Python setup/security/harness checks and 64 Maven domain/characterization tests, all with zero failures, errors or skips. Twelve Surefire report files are consistent with the Maven output.
- Artifact hashes in the summary match the current candidate-agent workspace:
  - WAR: bdd09e5ae195ae24df689920b999e1782228d50fd892b3f288faf8f1199f67ca
  - candidate-security JAR: 143fe10e2d185922c20ce4a252b3bb778a99df7e02cca3362b43e2427c068951
  - revision marker: fd90fa96499b7ddd0c60f453dc04df0d474675c233b4fcf8b89638c86ef49903
- The evidence correctly limits its claim to the SCM build/package and automated test path; it does not claim deployment, a separate PostgreSQL/WildFly/Chromium rerun, or production readiness. KAN-18 remains In Progress.

## Limitation

The reviewer could not enumerate artifacts through Jenkins' artifact API because anonymous access returned HTTP 403. It independently matched the artifact hashes against the candidate-agent workspace and found no contradictory log evidence.
