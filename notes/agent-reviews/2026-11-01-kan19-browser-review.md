# Independent agent review: KAN-19 browser increment

1 November 2026. Author /root; fresh-context read-only reviewer /root/review_kan19_browser. Base2ba277a1e3fec819aab94e4310f7d5980dc8edce.

Scope: new/updated Faces pages/template, CargoPages and missing-cargo exception, transactional role-guarded facade/EJB booking service, Cargo/Delivery empty-itinerary correction, explicit static-resource policy, pinned browser driver and runtime hook, tests, failure/final evidence, documentation/status records. Historical source and synced files preserved.

## Finding and correction

Material source finding: replacing singleton identity with empty-value NOT_ROUTED semantics initially conflicted with CargoTest's synthetic empty assigned good/bad routes, so existing domain tests failed. Author corrected good/bad fixtures to real nonempty itineraries, retained all original NOT_ROUTED/MISROUTED/ROUTED assertions, and added explicit independent-empty regression. Reviewer rechecked source and final Surefire evidence: CargoTest9/9 PASS; total domain35 with no failure/error/skip. One inherited empty TODO remains disclosed. No assertion was removed to obtain a pass.

Actual browser findings preserved separately: lazy DTO collections required a transaction around assembly; f:metadata belongs to the template client facet; a shared empty itinerary caused Hibernate collection-owner failure. Corrected in candidate only, with multiple real browser bookings/readback. Initial tmpfs report-collection harness failure was fixed by reading sanitized output from a running browser container.

Non-material stale report scope corrected to include current Faces routes. Reviewed strict static file/library mapping and query deny rules; no blanket dynamic-resource exemption.

## Final verification

- All250 recorded input hashes match current files.
- Independently reran six mocked cleanup regressions: PASS. Inspected browser timeout/failure/removal tests, npm lock and exact image pin.
- Inspected full30/30 Chromium and35/35 application reports,35 domain aggregate zero failures/errors/skips, cleanup and private-file removal. Reviewer did not rerun Docker or mutate services.
- Reviewed functional/architecture/technical documentation and bounded mobile/Chromium claims; git diff --check and JavaScript syntax check passed.
- Evidence SHA-256: validation.json45989a5763ddd6c7f733dbd64530fdbbbcb7eaba89ea7b5f77384529af96be71; browser-results.jsondcb104a5ca25583eff09d4ea65beb09b54eb8ff014fbcb63387c38c175ce9660; application-results.json7f5d0b883194d885efabf98029a056f74be480166c97f71a0726b45cd791d8fe.

Verdict: **no remaining material findings for this bounded increment**. Full KAN-19 acceptance remains unmet: routing, live tracking/WebSocket lifecycle, legacy mobile logger and independent denied-write database/queue/audit absence remain open. KAN-15/KAN-18/KAN-19 stay In Progress; KAN-14's502 cases stay BLOCKED. No publication or acceptance waiver claimed.

[Jira KAN-19](https://ai-modernization.atlassian.net/browse/KAN-19), [workflow documentation](../../docs/candidate/browser-workflows.md), [validation](../evidence/kan-19-browser/validation.json).
