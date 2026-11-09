# KAN-18 PostgreSQL/WildFly runtime evidence

`runtime.json` is the sanitized receipt from the successful disposable KAN-18/KAN-15 BG-06 integration run on 10 November 2026. It records the pinned component versions, fresh migration history, role separation, DML/DDL permissions, anonymous denial, three human test roles, no-seed/no-ORM-DDL startup behavior, restart persistence, source hashes and cleanup outcome.

The app was deployed from the candidate WAR with its default `META-INF/persistence.xml` descriptor; the test did not substitute the H2 runtime descriptor. PostgreSQL was not published to the host. The app used a separate non-internal Docker bridge to make its localhost-only `127.0.0.1:8082` endpoint reachable. That bridge permits outbound access from the disposable app container.

This receipt covers a fresh synthetic database only. It does not prove import of retained legacy data, a full populated-schema upgrade in the WildFly runtime, production migration, or external deployment. Independent post-run review approved the implementation and evidence.
