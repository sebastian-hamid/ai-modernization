# Cargo Tracker baseline investigation
Verified 23 October 2026.

## Source and preservation
- Existing clone: experiments/legacy-cargotracker.
- Origin: https://github.com/javaee/cargotracker.git.
- Exact commit: 57fc7b32d2597e43b5e0d454e707e0146de5258a (Update CONTRIBUTING.md).
- Upstream checkout is clean and was left unchanged.
- Build used a git archive copy under ignored .work/baseline/source; it did not build directly in the original checkout.

## Requirements observed in source
- Maven WAR, Java EE 7 API, compiler source/target 1.7 and endorsed-directory configuration.
- Default Maven profile glassfish; Cargo plugin targets GlassFish 4.1. A WebLogic profile also exists.
- README mentions WildFly, but this checkout's POM does not define that profile: do not follow that command without reconciliation.
- JPA uses java:app/jdbc/CargoTrackerDatabase; README describes Derby and schema/data reset at restart.
- Nine *Test.java files and 28 @Test annotations exist. These counts are inventory, not successful executions; some test methods are TODOs.
- Domain tests can run without a server; Arquillian service/scenario tests require a running application server.
- Surefire sets skipTests=true in the POM. A green package build alone would not establish test coverage.

## Initial build experiment (before recovery)
Container toolchain: Maven 3.10.0, Temurin Java 1.8.0_504.
Pinned image:
    maven@sha256:b9fac8295f9d342af5d815888dca1334b12833a84c870c260b88f31285c1ef3d

Java 8 is an isolation choice to test the old Java 7 compiler target/endorsed setup; successful GlassFish compatibility is not yet established. Host development remains Java 21.

Command in archived source, inside that image:
    mvn -B -ntp -Dmaven.repo.local=/workspace/.m2 package

Result: EXIT 1, dependency resolution failed before compilation. See [original build log](evidence/legacy-package-original.log) and [toolchain](evidence/legacy-toolchain.txt).

Unresolved artifacts included:
- org.primefaces.themes:ui-lightness:1.0.10
- org.eclipse.persistence:org.eclipse.persistence.antlr:2.3.2
- org.eclipse.persistence:org.eclipse.persistence.moxy:2.5.0-M13

Original repository URLs use HTTP and trigger Maven's HTTP blocker. Transitive maven.java.net HTTPS endpoints also produced certificate-chain errors. Direct checks found HTTP 403 for the PrimeFaces theme POM at its HTTPS repository, and HTTP 404 at Maven Central for each of the three exact POM coordinates. No TLS checks or HTTP protection were disabled.

## Recovered source baseline: PASS
On 23 October 2026, the fresh-export recovery script completed packaging and domain tests.

- Original application POM/source and all requested dependency versions are unchanged.
- Exact EclipseLink artifacts resolve through https://download.eclipse.org/rt/eclipselink/maven.repo/ using a repository-local settings file.
- Obsolete non-Eclipse repository IDs map to HTTPS Maven Central. TLS verification and Maven HTTP blocking stay enabled; no user-global Maven settings were edited.
- PrimeFaces ui-lightness 1.0.10 was rebuilt from official themes release tag 1_0_10, commit db6195c272cd7b2567c60b4ed786e44bbecf5db0.
- Its missing maven-jsf-plugin 1.3.0 was first rebuilt from official tag 1_3_0, commit 60774367fba1287c2a838ac78799b32c563c0acf.
- Both builds use unmodified tag source. This is a recovered source baseline; byte-for-byte equivalence to unavailable published PrimeFaces JARs is NOT established.
- Build-plugin tests are explicitly skipped: its JUnit 4.4 is incompatible with the image's default Surefire. This does not skip the Cargo Tracker domain test run.
- cargo-tracker.war packages successfully using the unchanged application POM (which skips tests).
- A separate domain-tests-pom.xml changes only skipTests from true to false. It runs an explicit list of five domain test classes, excluding server-dependent Arquillian tests.
- Outcome: 24 tests, 0 failures, 0 errors, 0 skipped. One reported test, ItineraryTest.testNextExpectedEvent, is an empty TODO; coverage remains limited.

| Test class | Reported tests |
| --- | ---: |
| CargoTest | 9 |
| ItineraryTest | 3 |
| RouteSpecificationTest | 4 |
| HandlingEventTest | 6 |
| HandlingHistoryTest | 2 |

## Reproduce the passing milestone
From the project root in Ubuntu:

    bash infrastructure/recover-legacy-baseline.sh

Requires WSL Python 3, Git, Docker access and network access to GitHub, Docker Hub, Maven Central and Eclipse downloads. It creates a fresh ignored source export; shared downloaded dependencies live under ignored .work/m2. It prints the WAR and timestamped evidence paths.

The original check-legacy-baseline.sh remains available to reproduce the earlier build without recovery. It is expected to fail resolving the old repositories.

Latest evidence: [recovered baseline run](evidence/recovered-baseline-20261023-073040.G1UReI/dependency-provenance.json). The same folder includes package.log, domain-tests.log, the exact POM overlay diff, toolchain information and the five Surefire XML reports. Dependency origins and SHA-256 hashes are recorded in the manifest; hashes are observations of recovered files, not publisher signatures.

## Runtime milestone completed
See [legacy-runtime.md](legacy-runtime.md) for the running application, the precise GlassFish HK2-277 module-metadata correction, reproducible commands and reports.

Four Arquillian booking tests passed against GlassFish. HTTP smoke checks covered page rendering, ABC123 tracking, candidate routes and a JMS-processed handling event. Three other legacy test classes contain unfinished setup and no runnable test annotations; they are coverage gaps, not passing tests.

The isolated Jenkins baseline pipeline now passes; see [jenkins-baseline.md](jenkins-baseline.md). Next review/version the scripts and extend behavior characterization before modernization.

References:
- [Maven HTTP repository policy](https://maven.apache.org/docs/3.8.1/release-notes.html)
- [Official Maven image](https://hub.docker.com/_/maven)

- [Official PrimeFaces theme release source](https://github.com/primefaces/themes/tree/db6195c272cd7b2567c60b4ed786e44bbecf5db0)
- [Official PrimeFaces build-plugin source](https://github.com/primefaces/maven-jsf-plugin/tree/60774367fba1287c2a838ac78799b32c563c0acf)
- [EclipseLink publisher repository](https://download.eclipse.org/rt/eclipselink/maven.repo/)
