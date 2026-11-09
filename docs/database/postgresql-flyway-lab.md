# PostgreSQL and Flyway lab workflow (KAN-22)

This Compose project is a disposable-development setup for the modernized candidate. It has an internal Docker network and publishes no PostgreSQL host port. The PostgreSQL volume persists across ordinary restarts. Do not point it at retained or production data.

## Secrets

Create a private directory, then generate three different password files named `bootstrap_password`, `app_password`, and `migrator_password`. The parent directory should be mode 0700. Because Docker Desktop's WSL secret mount is read by the PostgreSQL image during initialization, the files should be mode 0644 under that private parent. Set `KAN22_SECRET_DIR` to the absolute directory path; secret values are never stored in the repository.

## Fresh database

Start PostgreSQL and wait for its health check:

```sh
docker compose -f infrastructure/database/compose.yaml up -d postgres
```

Apply the immutable Flyway migrations as a one-shot job:

```sh
docker compose -f infrastructure/database/compose.yaml --profile migrate run --rm migrate
```

V1 creates the runtime schema. V2 adds query indexes and reconciles the shared ID sequence from imported IDs plus `legacy_sequence_state`. V3 grants DML only on the six runtime entity tables and sequence use to `cargo_app`. Flyway history and legacy migration state remain owned by `schema_migrator`.

The app role must not be granted schema creation or default CRUD on every table. When future migrations add runtime tables or sequences, add explicit grants in that migration.

## V1, import, then upgrade

When imported IDs must be preserved, apply V1 alone by setting `KAN22_MIGRATIONS_DIR` to a directory containing only `V1__initial_schema.sql`, then run the one-shot migrate job. Import rows with a separately reviewed importer, preserving DATE and timestamp semantics and validating all foreign keys. Include the legacy sequence counter in `cargo.legacy_sequence_state`. Clear `KAN22_MIGRATIONS_DIR` so Flyway sees the complete checked-in migration directory, then run migrate again to apply V2 and V3. Confirm row counts and representative values before and after and confirm the next shared ID exceeds every imported ID and legacy sequence counter.

No production-data importer or rehearsal is included in KAN-22. The tested upgrade uses only synthetic rows in a private disposable database.

## Disposable contract verification

The KAN-22 acceptance run used unique Compose projects and generated secrets under private `/tmp` directories. It verified fresh V1/V2/V3 installation; V1-only import followed by V2/V3; six-table row preservation; DATE round-trip; sequence high-water; app DML; persistent and temporary-table DDL denial; and denied updates to Flyway history and legacy sequence state. Clean up the exact test project with `docker compose ... down --volumes --remove-orphans` and delete its generated secret directory.

Never run `down --volumes` against a project that may hold retained or production data.

Before importing legacy SMALLINT flags into primitive Java booleans, reject or resolve NULL and every value other than 0 or 1. This data audit is not part of the synthetic KAN-22 fixture.

Fresh disposable verification also confirmed transaction rollback and that committed data survived a PostgreSQL container restart on its named volume.
