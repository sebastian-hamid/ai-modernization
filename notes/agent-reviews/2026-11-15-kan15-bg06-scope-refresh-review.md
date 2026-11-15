# Independent review: KAN-15 BG-06 scoped evidence refresh

**Date:** 15 November 2026  
**Verdict:** Approved  
**Reviewer:** Separate independent Codex review agent (`/root/review_service04_adapter`)

## Scope and evidence

- Starting revision: `7695459` (`Restore public typed cargo tracking`).
- Fresh scoped run: `kan18pg-4e9aed9134`.
- Persisted receipt: `notes/evidence/kan-15-bg06-scope/validation.json`.
- Persisted receipt SHA-256: `04a1377e44b421207c69272b1252be337e502dc78f8bc4f1e57807e6d2e9f956`.
- Raw runtime receipt SHA-256: `b6907de20838724be42549a51f6cb51ee55f7996e20a90ce9ffd2e4e5dcb1b57`.
- The fresh receipt binds all 208 source hashes and 14 schema/fixture hashes to revision `7695459`.

## Checks performed

- Matched the persisted run ID and raw receipt digest to the fixture output.
- Confirmed all source and schema hashes match the current committed tree.
- Confirmed the exact four human BG-06 denials and the `schema_migrator` Flyway machine case pass (5/5), with no validation reasons.
- Confirmed runtime status and exit code pass; owned containers, networks, volumes, probes, image and work files were removed. Generated secrets were not preserved.
- Ran `tests/security/test_bg06_startup_boundary.py`: all 8 tests pass.

## Limitations

The remote JMS probe remains connect/list-only and did not send or consume messages, so destination-level authorization is not established. This scoped receipt does not close KAN-15. The prior supplemental replay remains historical; a new replay must pin this receipt before using it for current-gate promotion.
