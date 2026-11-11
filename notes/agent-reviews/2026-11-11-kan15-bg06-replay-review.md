# KAN-15 BG-06 supplemental aggregate replay review

- Task: Reconcile only the five independently reviewed BG-06 results into a supplemental view of the last aggregate current-capability gate.
- Source revision: `087fbf2` (`Record BG-06 independent review and handoff`).
- Author: `/root`.
- Separate reviewer: `/root/review_kan18_postgres_prerun`.
- Review date: 2026-11-11.
- Implementation: `tests/security/replay_bg06_scoped_gate.py`.
- Focused tests: `tests/security/test_replay_bg06_scope.py` (6 tests passed).
- Baseline gate SHA-256: `e8b0119a7e40a2d8af4c854aec084754d2b47aee94d291ab31e7e8f424981622`.
- Scoped receipt SHA-256: `1563504790c838d8c43fed9128dbc5356b8a9fcb8bbc3714e11525c016a0df13`.
- Supplemental output SHA-256: `7ff15ff617bcbfe51be42b4652ce4f90c0b7bfa90cfd9bc19a2a5c769bd4aa04`.
- Output: `notes/evidence/kan-15-bg06-scope/current-capability-replay.json`.

## Review findings and response

The reviewer identified a provenance gap: the replay did not bind the supplied scoped receipt to its independently reviewed digest. The implementation now pins and checks the exact SHA-256 values for the baseline gate, scoped receipt, raw runtime receipt, BG-06 gate adapter, and independent BG-06 review record. CLI overrides fail unless the bytes match those reviewed artifacts.

Additional focused tests now assert that a one-byte modified receipt is rejected, exactly five BG-06 rows are promoted, the 449/21 counts become 454/16, and the hashes/counts for untouched current rows, all legacy rows, and all retirement rows match the baseline. Tautological self-comparisons were removed.

## Verification and verdict

- Python compilation passed; all six focused replay tests passed; `git diff --check` passed.
- Replay ran offline and did not launch a runtime or browser fixture.
- Output promotes only four human BG-06 denials and the BG-06-MACHINE migration case. It preserves the original source gate and records aggregate gate exit 2 because 16 current cases and 76 retirement cases remain blocked.
- The independent reviewer verified the pinned inputs, exact five-case promotion, unchanged-row hashes/counts, and scope limitations.
- Verdict: approved for commit as a supplemental replay.

## Limitations

This is not a new aggregate runtime run and does not close full KAN-15. The BG-06 remote JMS probe was connect/list-only and does not prove destination-level send/consume authorization. The historical audit and retirement results were preserved unchanged.
