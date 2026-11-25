# KAN-13 Java maintenance patch verification

Verified 25 November 2026 in an isolated copy of the spike harness. The source receipts from 1 November remain unchanged.

## Result

- Outcome: **PASS**, 19/19 checks passed.
- Runtime: Temurin 25.0.5.1+2; non-root UID 1000.
- WAR SHA-256: e5c36dc19eb3b256b7dc4c6db8a2b1e71fc2fbe87b828c98e8aa2d699606e9a7.
- Runtime image ID: sha256:25064874cd9512bc8319b9c32cc137f4a9a40a559cae19250060e9f2877fb0bb.
- Cleanup: PASS; no cleanup errors.
- JUnit: [TEST-kan13-runtime.xml](TEST-kan13-runtime.xml); full sanitized observations: [results.json](results.json).

## Checks

- Non-root runtime: PASS
- Anonymous API denied: PASS
- Wrong password denied: PASS
- reader permitted read on Java 25: PASS
- operator permitted read on Java 25: PASS
- admin permitted read on Java 25: PASS
- Anonymous Faces denied: PASS
- Faces/CDI expression rendered: PASS
- Reader mutation denied: PASS
- Anonymous mutation denied: PASS
- Denied requests did not create records: PASS
- operator allowed submit: PASS
- operator JPA/JMS/batch complete: PASS
- admin allowed submit: PASS
- admin JPA/JMS/batch complete: PASS
- Exactly two authorized records: PASS
- Missing record returns 404: PASS
- Unsupported method rejected: PASS
- Compiled Java 25 bytecode: PASS

## Scope

This proves the minimal Java/WildFly Jakarta EE capability fixture still runs against the patched JDK. It does not establish Cargo Tracker compatibility, full migration readiness, PostgreSQL/Flyway behavior, or a formal Jakarta EE 11 TCK result on Java 25. Existing 1 November run results are historical and were not overwritten.

Patch source: [Adoptium November 2026 CSPU](https://adoptium.net/news/2026/11/temurin-november-2026-cspu-java4shell), which identifies Temurin 25.0.5.1+2 and 21.0.13.1+2 as patched builds.
