# KAN-18 legacy-data rehearsal note review

Date: 23 November 2026

## Scope and reviewed inputs

- Task: KAN-18 disposable legacy-data migration rehearsal evidence.
- Repository revision before this documentation change: `55ca7947bf4e8d4a617b89c18e913ad76589a935`.
- Reviewed file: `notes/evidence/kan-18-legacy-data-migration-rehearsal.md`.
- SHA-256: `cd3e50462594e1c771223dec52c9144f711ac300060bf8c8b46e258b188dcb50`.
- Separate reviewer: `/root/review_kan18_data_rehearsal_note`.

## Checks performed

The reviewer inspected the rehearsal profile, import SQL, verification SQL and target export SQL in the ignored task-local work area. They independently compared all seven source/target CSV pairs; every pair had the expected row count and zero field mismatches after normalizing only Derby/PostgreSQL boolean spellings and timestamp text formatting.

The reviewer confirmed in the recorded verification output: 18/18 foreign keys validated, Flyway at version 6, both explicit orphan checks at zero, cargo flag and enum distributions consistent with the note, legacy sequence state 100, and PostgreSQL sequence `last_value=100` with `is_called=true`. The import SQL uses one transaction with deferred constraints and explicit table/column mappings.

The reviewer did not read credentials, modify files, or access or modify services. The author also ran `git diff --check`.

## Findings and verdict

No actionable findings. The reviewed note accurately limits its claim to generated legacy sample data and leaves retained-data profiling and reconciliation open. This review does not establish that real retained or production data has been migrated.
