# KAN-15 BG-06 scoped verification review

- Task: Verify the candidate's startup seed/reseed/schema-DDL boundary for the four human actors and the separate Flyway migration machine identity.
- Base revision: `5f71a4b` (`Document WildFly control-plane interfaces`).
- Published implementation/evidence: `92aebd3` (`Verify BG-06 startup and migration boundary`).
- Documentation follow-up: `6997a80` (`Document scoped BG-06 verification result`).
- Author: `/root`.
- Separate reviewer: `/root/review_kan18_postgres_prerun`.
- Review date: 2026-11-11.
- Evidence: `notes/evidence/kan-15-bg06-scope/validation.json`; fresh fixture run `kan18pg-4295cb899c`.
- Persisted evidence SHA-256: `1563504790c838d8c43fed9128dbc5356b8a9fcb8bbc3714e11525c016a0df13`.
- Runtime receipt SHA-256: `e310e0fab53caad06d8072934865746dd12b15360700d3565f7164cd4da54f9b`.
- Gate adapter SHA-256: `ea70c54464939615712bd256fe820741b7f724d865be15d13db16e98f547048c`.

## Review and corrections

The independent reviewer inspected the runtime changes, scoped gate adapter, source inventory checks, and final persisted receipt. Findings were resolved before publication:

1. Add the Faces/XHTML view layer to the hashed source inventory and scan its EL expressions; fix an over-escaped expression matcher and assert a representative expression is inspected.
2. Bind the four human and migration machine cases to the canonical desired-case ID, surface, actor, outcome, write flag, trusted-driver/isolated-fixture requirements, path, method, source text, and machine scope.
3. Persist and validate the exact 14-file schema/migration/fixture SHA-256 set; the initial compact evidence had referenced the ignored raw receipt but omitted those hashes.

The reviewer rechecked the corrections before each bounded fixture run. The final post-run review confirmed the persisted receipt matches the current raw runtime receipt and adapter, all 207 BG-06 source hashes and 14 schema/fixture hashes match the worktree, all five case IDs pass, there are no validation reasons, and cleanup is complete. The documentation follow-up was separately reviewed and approved.

## Verification

- Python compilation passed for the scoped adapter, runtime verifier and boundary tests.
- All 8 BG-06 static source/config regression tests passed.
- Fresh scoped gate: 5/5 PASS, exit 0.
- Cleanup: compose down and resource checks passed; no residual containers, networks or volumes; probes/image/work removed; generated secrets not preserved.
- `git diff --check` passed before publication.
- Commits `92aebd3` and `6997a80` were pushed to `main`; worktree was clean after each push.

## Verdict and limits

Approved for publication within the BG-06 scope. This does not close full KAN-15, refresh the aggregate current-capability gate, or establish destination-level JMS send/consume authorization. The JMS probe performed no sends or consumes. The Administrator handling-event import remains under BG-01/BG-02.
