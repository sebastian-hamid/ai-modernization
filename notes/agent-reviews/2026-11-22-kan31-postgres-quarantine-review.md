# KAN-31 PostgreSQL quarantine independent review

- **Verdict:** PASS, with disclosed non-material notes.
- **Reviewer:** independent agent `/root/review_kan31_final`.
- **Reviewed:** 22 November 2026.
- **Base HEAD:** `61d5b2cf7ab38018f09cde57dcd8ed2abb1fcba7`.
- **Tracked diff SHA-256:** `b979cc2a7c1e761c3803c00266b435401e88ea5c87b8076ed85b2caefe1d9ad6` (does not include untracked files).
- **Evidence:** disposable run `kan31q-da9cd525`, 46/46 runtime assertions, 63 Maven tests (0 failures/errors/skips), clean teardown. The implementation agent executed the run; the reviewer inspected the receipt and did not rerun tests.

## Review findings

Earlier review findings for replay re-quarantine, expiry visibility/replay, per-message pending markers, and alert state during multiple blocked transfers are addressed. The current callback and transfer paths acquire the request identity before the capacity-state row; pending-marker resolution and retention do not take the locks in reverse order. The reviewer found no lock-order cycle. The late-callback guard checks that the request remains `QUEUED` before adding a marker.

The callback ordering race is not deterministically forced by the runtime assertions. Evidence explicitly distinguishes runtime verification from code/characterization safeguards.

Legacy messages without a request ID or broker message ID use a deterministic fallback from registration time plus canonical payload. Identical payloads with identical registration timestamps cannot be distinguished. This bounded compatibility limitation is documented; new producers attach unique message keys. Reviewer accepted this as non-blocking.

The reviewer inspected updated evidence, verifier assertions, replay/expiry paths, capacity alert code, docs, and task log. `git diff --check` passed. Synced `sources/`, historical legacy source, and `Jenkinsfile` have no working-tree changes.
