# PostgreSQL backup, restore, and rollback rehearsal (KAN-28)

All rehearsals use a disposable Compose project and synthetic rows. Never run restore or cleanup commands against the retained demo database or production.

## Restore procedure

Create a custom-format archive while the source is at the desired migration version:

```sh
docker exec <postgres-container> pg_dump -Fc -f /tmp/cargo.dump -U db_bootstrap -d cargotracker
```

Restore into a separate target database, then apply the checked-in ownership and least-privilege ACL repair before application use or Flyway:

```sh
docker exec <postgres-container> createdb -U db_bootstrap restore_v3
docker exec <postgres-container> pg_restore --no-owner --exit-on-error -U db_bootstrap -d restore_v3 /tmp/cargo.dump
docker exec -i <postgres-container> psql -U db_bootstrap -d restore_v3 -v restore_db=restore_v3 < infrastructure/database/restore/restore-permissions.sql
```

The restore ACL script revokes PUBLIC database CREATE/TEMPORARY, grants CONNECT to the application and migration roles, makes `schema_migrator` the owner of the Cargo schema, runtime tables, Flyway history and shared sequence, and restores `cargo_app` runtime DML/sequence grants. It intentionally enumerates the V1-V3 schema objects; update and test it alongside future schema changes.

Verify marker rows, Flyway history, runtime-role access, and migration continuation before cutover. Run the candidate Flyway image against the restored database and confirm the next release migration succeeds. Do not direct traffic to a restored database until the application version and schema compatibility are checked.

## Rollback rehearsal

Take a V1 custom-format snapshot before applying later migrations. Restore it to a separate rollback database, apply the restore ACL script, and confirm the V1 marker/history. Keep the newer active database separate. Then rehearse the later migration chain against the restored copy; a successful migration demonstrates recoverability of the schema state, not compatibility of an older application binary.

Never attempt an in-place downgrade unless a separately reviewed migration explicitly supports it.

## KAN-28 test result and limits

The disposable PostgreSQL 18.6 / Flyway 13.12.1 rehearsal passed. A V1 archive restored with synthetic marker id 4501 and Flyway version 1. The separate active database remained at version 3. After applying the restore ACL script, `schema_migrator` applied V2 and V3 and a temporary V4 probe migration; the restored DB reached version 4. `cargo_app` successfully inserted an explicit synthetic row after restoration and migration.

A V3 archive restored with marker id 4501 at version 3. The same ACL script was applied; `cargo_app` read the marker and `schema_migrator` applied the temporary V4 probe migration. The named-volume restart retained the active V3 marker, and it remained readable after restart.

The rehearsal ran on one WSL/Docker host and one PostgreSQL version. It did not test encrypted off-host storage, scheduled backup automation, point-in-time recovery, cross-version restoration, production-sized data, or an actual older WildFly binary against a rolled-back schema. The test archives and disposable Compose project were removed after verification.
