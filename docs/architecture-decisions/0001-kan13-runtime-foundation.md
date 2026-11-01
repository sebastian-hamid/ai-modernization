# ADR 0001: candidate runtime foundation

1 November 2026. Status: recorded compatibility conclusion after separate-agent review; no remaining findings. User already selected layered WAR, latest compatible LTS Java, Jakarta EE 11 and standard WildFly. KAN-13 verifies a minimal combination without changing the historical baseline.

Decision: continue with standard WildFly 42.0.0.Final full configuration on pinned Temurin Java 25.0.5+8. The official server base's older Java patch is replaced with the JDK from the pinned Maven image; the Dockerfile records both immutable digests. Use the exact compiler/API/plugin versions in spikes/kan13-runtime/pom.xml. No framework fallback, Preview server or database migration was needed.

Evidence: [spike run and scope](../../spikes/kan13-runtime/README.md), [19 check results](../../notes/evidence/kan-13-runtime/results.json), [JUnit report](../../notes/evidence/kan-13-runtime/TEST-kan13-runtime.xml). Checks execute REST/EJB authentication/roles, JPA/H2, JMS/MDB, Faces/CDI and batch, then remove the disposable runtime.

Consequences: we have a headless Linux candidate foundation for further work, not a migrated Cargo Tracker build. The assembled JDK/server image is tested here but is not a formal EE-on-Java-25 compatibility claim. PostgreSQL/Flyway, full entity mapping, PrimeFaces/mobile, browser/session/CSRF/WebSocket, resilient restarts and complete KAN-12 security requirements remain unproven. H2 auto-schema generation and BASIC authentication are disposable probe choices, not changes to the approved target persistence/session plan. Future updates require pinned rebuild and regression checks.

[Independent review and limits](../../notes/agent-reviews/2026-11-01-kan-13-runtime-review.md). This closes the minimal spike criteria and does not assert full application migration.
