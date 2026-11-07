# Booking replacement capability evidence

This KAN-15 increment adds the strict booking-deadline and single-page booking groups. It covers four actors in each group. Operator and Administrator must reject an invalid calendar deadline, submit a valid booking, and preserve origin, destination, and deadline on the same current form. Reader is denied with 403 and no booking payload. Anonymous access redirects to the configured login page without booking fields.

All eight actor intervals cover four invalid deadline POSTs and four direct source-denial GETs for Reader and anonymous. Each has independent before and after observations. Database tables, queues, and service invocation counters remain unchanged. The observer getAllCargo counter has a zero delta in these intervals.

For each permitted booking, the browser records the actual form POST and validates the same-origin booking endpoint. It parses the redirect Location against the POST URL and requires both that redirect and the committed details URL to identify the same cargo. The tracking ID shown in the page must match the redirect ID. An independent Reader checks the saved origin and destination through the cargo API and checks the deadline on the details page. The two permitted bookings produce positive snapshots, referenced by both groups, bound to the same fixture as each actor's invalid attempt and show a database change, unchanged queues, one bookNewCargo invocation, one independent getAllCargo read, and unchanged other invocation counters.

Fresh runtime results were 661 native checks and 669 browser checks, all passing. The two groups add eight passing cases. Current coverage is **400 PASS / 70 BLOCKED**. Historical audit remains **324 PASS / 178 BLOCKED**. All 76 retirement checks remain BLOCKED. The fixture removed its application container, browser container, private files, and network with no cleanup errors.

The runner fingerprints on-disk inputs and constructed contracts. Imported Python code identity is not attested. The browser output retains sanitized booleans rather than raw redirect URLs or persisted-value strings, so the independent runtime reviewer verified the producer assertions and recorded receipts but could not reparse those original strings. The individual source hash manifest was reconstructed after the run and matched its recorded aggregate fingerprint. Unsupported replacement and internal-boundary cases remain BLOCKED.

See [sanitized validation](../../notes/evidence/kan-15-booking-replacements/validation.json).
