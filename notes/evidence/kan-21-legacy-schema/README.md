# KAN-21 legacy physical Derby schema

Date: 9 November 2026

## Scope and method

The pinned legacy WAR (source commit `57fc7b32d2597e43b5e0d454e707e0146de5258a`, WAR SHA-256 recorded in validation) was deployed in a fresh disposable GlassFish 4.1 container built with the previously documented HK2-277 metadata correction. Its default persistence configuration generated a new Derby database and the legacy sample-data startup bean ran only against that scratch database. The runtime used a private Docker bridge with no host ports published. After a graceful shutdown, the scratch database was copied and inspected offline with Derby 10.10.2.0 `dblook`. The temporary container was removed. The currently running demo and the pinned source checkout were not touched.

The published SQL contains schema only, no business row data. See [raw dblook DDL](legacy-derby-dblook.sql) and [validation manifest](validation.json).

## Observed schema

The physical `APP` schema has seven tables: CARRIER_MOVEMENT, VOYAGE, LEG, HANDLINGEVENT, SEQUENCE, CARGO and LOCATION. The export records seven primary keys, one unique constraint (CARGO.TRACKING_ID), eighteen foreign keys, no explicit secondary indexes, and no check constraints. The two SMALLINT flags on CARGO default to zero but are nullable in the physical DDL. Primary-key and relationship details are in the raw export.

The export confirms important physical facts that source annotations alone do not fully specify:

- `HANDLINGEVENT.COMPLETIONTIME` and `REGISTRATION` are SQL DATE. The source model declares `@Temporal(DATE)`; migration cannot recover time-of-day discarded before persistence.
- ETA and specification deadline are SQL DATE. Movement and leg schedule times and `CARGO.CALCULATED_AT` are SQL TIMESTAMP without timezone.
- Routing/transport/event enums are VARCHAR(255) values. Preserve exact stored strings and reject unmapped values; do not silently rename enum constants.
- `UNLOADED_AT_DEST` and `MISDIRECTED` are SMALLINT default 0, not SQL BOOLEAN. Validate source values are 0 or 1 before converting; preserve or explicitly reject NULL rather than silently coercing it.
- Entity identifiers are BIGINT. The legacy `SEQUENCE` table stores `SEQ_COUNT` as DECIMAL(15,0); a target migration must reconcile its generator state with the maximum migrated identifier to prevent collisions.
- Eighteen foreign keys describe references across cargo, events, legs, movements, voyages and locations. The cargo/event references form a cycle. A data load must order inserts and handle the cycle explicitly, for example by initially loading nullable references and updating them after both rows exist, or by using appropriately deferred constraints.
- Derby's generated constraint identifiers are run-specific. PostgreSQL migrations should define stable names. The export reports no standalone secondary indexes; KAN-22 should add indexes only from reviewed candidate query paths and measured needs.

## Recommended PostgreSQL mapping and conversion rules

Use explicit, versioned PostgreSQL DDL rather than asking Hibernate to create/alter production schemas. Keep canonical lowercase snake_case identifiers. Preserve all source identifier values and business keys. Map SQL DATE to PostgreSQL DATE; map timezone-less SQL TIMESTAMP to PostgreSQL `timestamp without time zone` and preserve wall-clock values, with any source timezone assumption recorded separately. Convert the two SMALLINT flags to BOOLEAN only after a data audit confirms values are limited to 0/1 and NULL treatment is approved. Retain enum strings exactly, with a staging validation that rejects unknown values. Treat `SEQUENCE` as legacy generator state, not automatically as an application table in the final model; select the replacement ID strategy and seed it above all imported IDs.

Before any real-data migration, KAN-22 or a follow-up must run reconciliation for source/target row counts, primary/unique key preservation, orphan references, flag values/nulls, enum values, identifier-generator state and date/timestamp boundaries. This schema-only fixture does not establish those real-data checks or prove production compatibility.

## Remaining scope

KAN-21's physical schema inventory and proposed mapping are documented. Actual retained-demo data profiling is deliberately not claimed. KAN-22 (PostgreSQL/Flyway) remains To Do, and KAN-18 remains In Progress; BG-06's distinct deployment/migration identity and no-destructive-startup acceptance still need an implementation-backed verification.
