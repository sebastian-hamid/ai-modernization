# Independent review: refreshed BG-06 scoped gate

- **Task and scope:** Refresh the KAN-15 BG-06 source-bound scoped gate and review related KAN-18 security test updates. This review does not complete KAN-18.
- **Baseline revision:** `b6dc76c82e114b86a4c918f72d04eb4188f38297`; reviewer inspected the current working diff and final refreshed evidence before any pin updates.
- **Author:** `/root`.
- **Independent reviewer:** `/root/review_kan18_probe_split`.
- **Review date:** 2026-11-23.

## Findings and responses

1. **P1, booking target route was not bound to current authorization semantics.** The source-hash drift allowance excludes the changing access-route manifest digest, so four booking retirement source checks could have accepted a public `/admin/book.xhtml` target. The author added exact unique `Operator,Administrator` route checks to the ACTION-26, ACTION-32, ACTION-27/30/34, and ACTION-28/31/33 source helpers, plus a temporary-root mutation test that changes the target route to `PUBLIC` and verifies all four helpers reject it. The reviewer confirmed the mutation test and final route checks. **Resolved.**
2. **P1, first refreshed receipt became stale after the startup test changed.** The reviewer found one mismatched source hash after the duplicate assertion cleanup. The author reran the full scoped gate against the final test file and independently compared every recorded fingerprint. **Resolved; only the second run is reviewed and pinned.**

## Final evidence reviewed

- Scoped run: `kan18pg-09dda23881`; gate result `PASS`, 5/5 cases, no reasons.
- Validation receipt: `notes/evidence/kan-15-bg06-scope/validation.json`, SHA-256 `e5045adb8aa237c956d706b21cc4817ec5af0bbd5ee0ea20b33ee84abd52ec89`.
- Raw runtime receipt: `.work/kan18-postgresql-last-result.json` (local ignored evidence), SHA-256 `405a16da18072bbdc1a3346c4257e1d20976a371a193b195b5dec2fd22ad8f80`.
- Gate adapter: `tests/security/run_bg06_scoped_gate.py`, SHA-256 `ea70c54464939615712bd256fe820741b7f724d865be15d13db16e98f547048c`.
- All 220 source fingerprints and all 14 schema fingerprints matched the current checkout. All 12 required runtime evidence checks passed.
- Cleanup evidence: Compose down, owned resources and image removed, probes and work directory removed, and no residual containers, networks, or volumes.
- Checks run by the author: route mutation and BG-06 startup tests passed 9/9; Python compilation and `git diff --check` passed.
- The reviewer inspected the current source diff and both receipts, verified validation/raw/adapter hashes and fingerprints, and found no credential values. The reviewer ’s final verdict was **PASS**, with no remaining material findings for this scoped change.

## Remaining limits

The receipt verifies only the five BG-06 human/machine boundary cases and their documented checks. It does not establish the complete KAN-15 acceptance set, full KAN-18 completion, destination-level JMS send/consume authorization, or resolution of the separate KAN-31 quarantine retry observation.
