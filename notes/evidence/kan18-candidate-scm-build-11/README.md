# KAN-18 candidate Jenkins build 11

Jenkins candidate SCM build 11 completed SUCCESS in 64.905 seconds on revision e153fe2873e3c68eb5215c62e8b14780487ac63c. It checked out the main repository revision exactly, fetched the legacy CargoTracker source at pinned commit 57fc7b32d2597e43b5e0d454e707e0146de5258a as a detached clean read-only checkout, and ran the candidate setup/security/harness and Maven build stages.

The Python checks reported 132 tests across setup, security-contract and harness suites; Maven reported 64 domain/characterization tests. All reported failures, errors and skips were zero. The build used Temurin 25.0.5.1, Maven 3.10.0, Python 3.14.4 and Git 2.53.0. Jenkins archived the candidate WAR, security JAR, revision marker and 12 Surefire reports. Artifact sizes and SHA-256 values are in summary.json.

This verifies the Jenkins SCM build and package/unit-test path. It does not deploy the WAR or rerun the separate PostgreSQL/WildFly/Chromium runtime suite, and it is not a production deployment. KAN-18 remains open pending remaining acceptance review and integrated runtime evidence. See http://localhost:8080/job/ai-modernization-candidate/11/ while the local Jenkins controller is running.
