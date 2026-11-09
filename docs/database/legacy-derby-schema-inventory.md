# Legacy Derby schema inventory (KAN-21)

**Status:** Reviewed physical schema generated from the pinned legacy WAR in a fresh disposable database. This is not a dump of retained demo data. PostgreSQL target DDL and real data conversion remain KAN-22 work.

## Evidence provenance

Source commit `57fc7b32d2597e43b5e0d454e707e0146de5258a`; WAR SHA-256 `0d0b70c6659466e023912c9d12bd215b15fbd44677b74ca6e57265bd7e067fae`. A fresh isolated GlassFish 4.1 runtime used Derby 10.10.2.0 and the documented narrow HK2-277 correction. After startup created the scratch schema and sample data, the runtime was gracefully stopped, the database copied, and the copy inspected offline. No host ports were published, and the running demo was not touched. Full details and schema-only DDL: [evidence folder](../../notes/evidence/kan-21-legacy-schema/).

## Physical mapping

| Derby table | Columns | Physical representation and relationships |
| --- | ---: | --- |
| CARRIER_MOVEMENT | 6 | BIGINT ID; departure/arrival TIMESTAMP; voyage and two location foreign keys |
| VOYAGE | 2 | BIGINT ID; VARCHAR voyage number |
| LEG | 7 | BIGINT ID; load/unload TIMESTAMP; voyage, cargo and two location foreign keys |
| HANDLINGEVENT | 7 | BIGINT ID; completion/registration DATE; VARCHAR type; cargo, location and voyage foreign keys |
| SEQUENCE | 2 | VARCHAR(50) name primary key; DECIMAL(15,0) counter |
| CARGO | 18 | BIGINT ID; date/timestamp fields; two nullable SMALLINT flags defaulting to 0; status/event VARCHAR fields; unique tracking ID; location/voyage/event references |
| LOCATION | 3 | BIGINT ID; VARCHAR name and UN/LOCODE |

Observed totals: 7 primary keys, 1 unique constraint on CARGO.TRACKING_ID, 18 foreign keys, no explicit standalone secondary indexes, and no check constraints. SQL details are authoritative in the dblook export; generated Derby constraint names are incidental and must not be reused as target names.

## Demo seeding and durable startup

The legacy source’s startup generator is destructive: it deletes existing rows and reseeds demo data, and its original persistence descriptor requests schema creation. The KAN-18 candidate separates this behavior in source: its [default persistence descriptor](../../candidate/cargotracker/src/main/resources/META-INF/persistence.xml) sets schema-generation action to `none`, and [SampleDataGenerator](../../candidate/cargotracker/src/main/java/net/java/cargotracker/application/util/SampleDataGenerator.java) returns unless the explicit `lab.candidate.disposable` property is enabled. Its test-only image instead uses an isolated database and an explicit disposable-lab flag. These are code/configuration facts, not a claim that retained-data restart behavior was tested against a durable PostgreSQL instance. Production deployment must not set the disposable flag.

## Conversion rules proposed for KAN-22

- Preserve BIGINT identifiers and tracking IDs. Reconcile the target generator above every imported identifier.
- Preserve DATE as DATE. HANDLINGEVENT timestamps have already lost time-of-day by the legacy `@Temporal(DATE)` mapping; do not invent it.
- Preserve timezone-less TIMESTAMP as PostgreSQL `timestamp without time zone`, retaining wall-clock fields. Record any actual source-timezone assumption separately.
- Audit SMALLINT flag values first; map only 0 and 1 to BOOLEAN. Preserve/reject NULL explicitly.
- Preserve enum VARCHAR strings exactly; fail migration on unknown values.
- Load the CARGO/HANDLINGEVENT reference cycle safely, using a staged nullable-reference update or verified deferred constraints.
- Use stable lowercase snake_case target names and explicit Flyway DDL. Add indexes from actual query needs rather than copying none or inventing them.

These are recommendations based on generated physical DDL and the legacy Java model. No real retained-database row counts, null distributions, enum inventory, orphan scan, or migration rehearsal has been performed. No PostgreSQL mapping or data migration is yet implemented.
