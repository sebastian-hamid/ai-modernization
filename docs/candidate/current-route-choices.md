# Current route choices and itinerary alias

KAN-15, 4 November 2026. ACTION-16 verifies selectable route choices for the selected cargo. ACTION-18 exercises the legacy itinerary URL as an entry to the same current page. The original historical callback observations remain separate.

The fixture reads the selected cargo's endpoints through an independent Reader session. For permitted roles it checks the real route form, route selector options, connected leg endpoints, and the same-origin refresh link carrying the exact selected ID. The alias must return the exact fixed local redirect before the target is requested. For denied roles, the alias and modern target are checked separately; denial may not expose cargo or route data. Each actor is also tested with missing, malformed and unknown tracking IDs. An authorized unknown-ID alias can redirect only to the fixed route page for that same ID, where it receives a 404.

The fixture compares settled database, queue and invocation snapshots before and after the group. Only the three exact planner read counters may change, each by four for the four allowed loads. An unexpected extra read, mutation call, database change, or queue change fails the check. ACTION-15 remains pending: the route page displays choices, but does not render the separately required cargo details.

The fresh fixture passed 650 native and 431 Chromium checks, including 24 invalid-ID cases. The current gate is **340 PASS / 130 BLOCKED**. The historical audit remains **324 PASS / 178 BLOCKED**, and all **76 retirement checks remain BLOCKED**. Gate exit is 2 because coverage is incomplete. The owned containers, private files and network were removed; the shared services stayed up.

See [sanitized evidence](../../notes/evidence/kan-15-route-choices/validation.json) and the [independent review record](../../notes/agent-reviews/2026-11-04-kan15-route-choices-review.json). The route HTML and cargo identifiers are not published. The remaining current blocks are 40 behavior cases, 44 replacement cases and 46 internal cases.
