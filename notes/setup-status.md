# Setup status
Verified 23 October 2026 (Europe/Bratislava). Checks ran on the actual WSL host, not the synced ChatGPT sources.

## Working
| Area | Evidence |
| --- | --- |
| WSL | Ubuntu-24.04 running as WSL version 2; Ubuntu 24.04.5 LTS; user yasinrdp. |
| Java | OpenJDK and javac 21.0.12.1. JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64. |
| Maven | Ubuntu Maven 3.8.7 at /usr/bin/mvn, home /usr/share/maven, uses Java 21. Verified fresh login and interactive shells. |
| Git | 2.43.0; main at 88e6479ea845745c362d567d55d1666acea05b49 before this work. |
| GitHub | gh authenticated as sebastian-hamid; origin https://github.com/sebastian-hamid/ai-modernization.git. Remote main matches local HEAD; repository is already PUBLIC. Visibility was not changed. Read access verified; no push performed. |
| Docker | Client/Engine 29.9.1, Docker Desktop 4.96.0; Compose v5.6.0. hello-world completed successfully. |
| Jenkins | Existing ai-modernization-jenkins container up, image jenkins/jenkins:lts-jdk21, version marker 2.580.1. Login endpoint returned HTTP 200 from Windows and Ubuntu. |
| Jenkins security | useSecurity=true; local user database; authenticated full-control authorization. Existing account record named jenkinsadmin. Configured URL http://localhost:8080/. |
| Jenkins storage | Existing Compose publishes 127.0.0.1:8080 and persists /var/jenkins_home in a named volume. Configuration was preserved. |

## Fixes applied
- Installed Ubuntu's maven package. Previously Maven resolved to /mnt/c/ProgramDev/apache-maven-3.9.11/bin/mvn; the Windows installation is unchanged.
- Added ~/.config/ai-modernization/java-env.sh and sourced it from ~/.profile and ~/.bashrc. This addresses JAVA_HOME in both login automation and interactive shells. Non-login scripts should source that file explicitly.
- Backed up shell files as ~/.profile.before-ai-modernization-20261023 and ~/.bashrc.before-ai-modernization-20261023.
- Added project .gitignore for experiments/, .work/, target directories and common secrets. Existing upstream checkout was neither deleted nor imported.
- Preserved docs/ and specifications/ instead of renaming them to match a proposed layout.
- Added baseline notes, logs and reproduction script. Initial setup made no commits or pushes. The reviewed setup is now versioned locally as baseline-v0.1.0; synced references remain untouched.

## Checks still requiring attention
1. Sign in to http://localhost:8080/ with your existing Jenkins account. No password was read or requested, and authenticated login was not tested.
2. Jenkins restart persistence is configured but was not exercised, to avoid interrupting the running controller. Plugin inventory and CI build-agent tools are unverified.
3. The reviewed setup is versioned locally as baseline-v0.1.0. Publishing it to GitHub and configuring SCM-triggered Jenkins execution remain separate steps.
4. Legacy packaging and domain tests now PASS after historical dependency recovery; see [legacy-baseline.md](legacy-baseline.md).
5. Runtime and booking integration now PASS: GlassFish 4.1 with the documented HK2-277 metadata correction, embedded Derby/JMS, four Arquillian booking tests, and HTTP tracking/routing/handling checks. See legacy-runtime.md. The isolated Jenkins baseline pipeline now passes; see jenkins-baseline.md.

## Useful verification commands
Run in a fresh Ubuntu shell:
    printenv JAVA_HOME
    command -v mvn
    java -version
    javac -version
    mvn -version
    cd /home/yasinrdp/projects/ai-modernization
    git status
    git ls-remote origin refs/heads/main
    docker compose -f infrastructure/compose.yaml ps

Do not use docker compose down -v: that would delete Jenkins data.

## Baseline recovery completed
A fresh source export built cargo-tracker.war successfully in the pinned Java 8/Maven container. Five domain test classes passed: 24 reported tests, zero failures/errors/skips; ItineraryTest.testNextExpectedEvent is an empty TODO.
Eclipse artifacts were recovered from their original publisher's HTTPS repository. The missing PrimeFaces theme and its build plugin were rebuilt from exact official release tags; published-binary equality is unverified. Application source, dependency versions and the upstream checkout are unchanged. A separate test POM changes only skipTests to false.
The recovery script, settings, provenance hashes and reports are in infrastructure/ and notes/evidence/. Runtime milestone is now complete on host port 8081; see legacy-runtime.md. The isolated Jenkins baseline pipeline now passes; see jenkins-baseline.md. Next: broader behavior characterization; local setup versioning is complete.

## Runtime milestone completed
The application is healthy at http://localhost:8081/cargo-tracker/. Four booking integration tests and tracking/routing/asynchronous-handling HTTP checks passed against the Compose-managed runtime. Original GlassFish deployment failure, the module-metadata correction and remaining coverage gaps are documented in [legacy-runtime.md](legacy-runtime.md).

## Jenkins milestone completed
Build 1 of ai-modernization-baseline finished SUCCESS in 99.495 seconds. It published 28 reported tests (24 domain + four booking; one empty TODO), passed HTTP workflow checks and archived the WAR/provenance. A separate non-root Java 21/Java 8 agent runs all builds; controller executors are zero. Source mode remains a local snapshot. The reviewed setup is versioned locally as baseline-v0.1.0; publication and SCM integration remain pending. See [jenkins-baseline.md](jenkins-baseline.md).

## Expanded handling coverage (26 October 2026)
See [handling-characterization.md](handling-characterization.md) for added factory and live workflow coverage, observed legacy defects, test counts and fixture limits. Jenkins restart and agent reconnection have now been exercised; interactive administrator login remains unverified.

Jenkins build 4: SUCCESS; 53 application cases and 10 tooling checks passed. See [build evidence](evidence/jenkins-build-4/summary.json). Remaining blockers include interactive Jenkins login verification, GitHub publication/SCM wiring, final JMS retry disposition, and disposable GlassFish restart recovery.

## Coverage/access review (27 October 2026)
Jenkins build 6 passed: 134 application cases and 10 tooling checks, including 81 new entrypoint contracts. The separate access-control requirement FAILED: anonymous data reads, handling writes and cross-origin WebSocket access are confirmed. See [coverage matrix, findings and remaining gaps](test-coverage-review.md). Production source and shared demo were preserved.

## Baseline documentation (28 October 2026)
Functional, architecture and technical baseline documents are available in [docs/baseline](../docs/baseline/README.md). This pass verified source references and archived evidence, not current service health or target compatibility.
