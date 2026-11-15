# Independent review: KAN-15 ACTION-26 retirement evidence

- Reviewer: `/root/review_action23_driver` (independent agent)
- Date: 2026-11-15
- Decision: **APPROVED for RETIRED classification**. RETIRED is not PASS.
- Ticket: KAN-15
- Legacy action: ACTION-26 PrimeFaces deadline `dateSelect` callback
- Replacement: `REPLACEMENT::booking-deadline`

## Evidence reviewed

Fresh isolated aggregate evidence: `notes/evidence/kan-15-action26-retirement/candidate-evidence.json` (SHA-256: `11262b6c1f64730ef3483d84e56b5ce92521ed3efa087ac20b5f5b85ef0e260e`). The run passed 777 aggregate checks and reported `private_files_removed=true`. All 470 current capability cases passed. Before this review, retirement counts were 12 RETIRED and 64 BLOCKED, with gate exit 2; all four ACTION-26 rows remained BLOCKED pending review.

The reviewer verified all four booking-deadline replacement cases PASS and independently recomputed the five source hashes. The historical page contains the PrimeFaces `dateSelect` listener for `dateForm:deadline` and the legacy `deadlineUpdated` method. The candidate booking page provides the typed deadline form. Its compatibility servlet maps the old GET URL to `/admin/book.xhtml` and has no POST handler; the access policy grants that route only to Operator and Administrator.

Fresh stale POST observations match the route boundary: Anonymous receives a 303 to configured login; Reader receives a 403 with server-verified Reader identity; Operator and Administrator receive 405 after using the current booking form, a valid CSRF token, and nonempty JSF ViewState. Each request targets the exact historical path and component, returns no protected cargo data, and leaves database, queues and business-invocation effects unchanged. All four proofs share the same 13-cargo snapshot hash.

## Decision and limits

Approve only the four ACTION-26 rows for **RETIRED**, never PASS. Keep all 470 current PASS results unchanged; retain all unrelated retirement outcomes. The overall gate remains exit 2 because other retirement cases remain BLOCKED. The evidence is a fresh owned-runtime run with verified fixture cleanup; imported-code identity was not independently attested. Offline replay must pin the exact evidence and review bytes and change only the four ACTION-26 rows.
