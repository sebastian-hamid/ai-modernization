# KAN-18 disposable legacy-data migration rehearsal

Date: 23 November 2026

## Scope

This is a controlled rehearsal using generated Cargo Tracker sample data, not a retained demo or production database export. The legacy sample database was created from a fresh deployment of the pinned historical WAR (source commit `57fc7b32d2597e43b5e0d454e707e0146de5258a`) in the previously documented GlassFish 4.1 validation image (`sha256:899f3ae0a00cc80fd9e8dd49d9104da4baf4aad81167754ac51c8c3b7a160e84`). The database copy was inspected offline. The historical source and synced `sources/` files were not modified.

The target was a new private PostgreSQL 18.6 Compose project named `kan18-legacy-rehearsal`, with no host port published. The database image was pinned by the existing Compose file. Generated credentials and all row exports were confined to ignored `.work/kan18-legacy-profile-20261123-a/`.

## Rehearsal procedure

1. Exported seven legacy tables from the offline Derby 10.10.2.0 database copy using explicit source-to-target column lists.
2. Converted the nullable legacy SMALLINT flags with explicit CASE expressions: 0 to false, 1 to true, and NULL to NULL. The generated sample contained only 0 and 1 for these flags.
3. Applied Flyway V1 alone to a new PostgreSQL database.
4. Imported all seven tables in one transaction with deferred constraints, preserving source IDs and nullable references.
5. Applied the complete checked-in Flyway migration set V2 through V6.

This was a one-off rehearsal. No reusable importer or production-data workflow was added.

## Results

| Legacy entity | Source rows | PostgreSQL rows |
| --- | ---: | ---: |
| LOCATION | 13 | 13 |
| VOYAGE | 5 | 5 |
| CARRIER_MOVEMENT | 13 | 13 |
| CARGO | 4 | 4 |
| LEG | 7 | 7 |
| HANDLINGEVENT | 12 | 12 |
| SEQUENCE / legacy_sequence_state | 1 | 1 |

- All 18 foreign-key constraints were present and validated after import. The explicit origin-location and handling-event-to-cargo orphan checks both returned zero.
- Every exported field in every row matched the PostgreSQL export. The comparison normalized only timestamp textual formatting and PostgreSQL's `t/f` versus Derby's `true/false` boolean spelling; it reported zero field mismatches across all seven tables.
- Cargo flags retained the observed values: `UNLOADED_AT_DEST` false for 4 rows; `MISDIRECTED` false for 3 rows and true for 1 row. There were no NULL flag values in this generated sample.
- Routing values retained: `MISROUTED` 1, `NOT_ROUTED` 1, `ROUTED` 2. Transport values retained: `CLAIMED`, `IN_PORT`, `NOT_RECEIVED`, and `ONBOARD_CARRIER`, one each. Handling-event values retained: `CLAIM` 1, `CUSTOMS` 1, `LOAD` 4, `RECEIVE` 3, `UNLOAD` 3.
- DATE and timezone-less timestamp fields matched row by row. Observed handling completion dates ranged from 2016-03-01 to 2016-10-27; leg load times from 2016-03-02 to 2016-10-24; cargo ETA was 2016-03-12. These are sample values only.
- Flyway reached version 6. V2 reconciled the shared ID sequence to 100 from the legacy generator state; PostgreSQL reported `last_value=100` and `is_called=true`, so the next generated value is 101.

## Limits and remaining acceptance

The generated sample has only four cargo rows and does not establish the shape or quality of any retained user data. It does not exercise NULL or out-of-range legacy flag values, unknown enums, corrupt/orphaned relationships, high-volume import performance, or operational recovery. It is not evidence that an arbitrary retained or production dataset is migratable. On 23 November 2026, the user confirmed that no retained legacy dataset exists for this project. Actual retained-data profiling, reconciliation, and import are therefore not applicable to the current modernization scope, rather than open blockers. The generated-sample rehearsal remains useful compatibility evidence only. If a real dataset is introduced in a future scope, its profiling, reconciliation, import, and recovery plan will need separate authorization and evidence.

The scratch Derby copy, CSV exports, generated secrets, temporary V1 directory, and isolated Compose database are task-local artifacts and must be removed after review. Keep only this aggregate evidence note in Git; do not publish sample row data or credentials.
