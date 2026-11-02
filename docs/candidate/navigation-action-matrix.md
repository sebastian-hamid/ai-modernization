# KAN-15 navigation action matrix

This bounded increment maps six historical navigation actions to the candidate's current UI. It covers 24 active-identity cases: anonymous, Reader, Operator and Administrator. Original inventory expressions identify legacy behavior; they are not claims that retired command links or old Faces callback code execute in the replacement UI. Internal templates remain inaccessible by direct HTTP.

| Inventory | Historical callback | Current control / target | Allowed |
| --- | --- | --- | --- |
| ACTION-01 | /admin/dashboard.xhtml | Cargo list / admin/dashboard.xhtml | Reader, Operator, Administrator |
| ACTION-02 | booking | Book cargo / admin/book.xhtml | Operator, Administrator |
| ACTION-03 | /admin/track.xhtml | Track cargo / admin/track.xhtml | Reader, Operator, Administrator |
| ACTION-04 | /admin/map.xhtml | Live tracking / admin/live.xhtml | Reader, Operator, Administrator |
| ACTION-05 | /admin/about.xhtml | Cargo workflows / admin/about.xhtml | Reader, Operator, Administrator |
| ACTION-06 | /public/about.xhtml | About / public/about.xhtml | Everyone |

The home page now includes an About link to the existing sanitized public description. Protected About is reached through Cargo workflows from the cargo list. Navigation labels reflect the modern candidate; the historical source inventory is preserved.

## Execution and proof

A shared, reviewed navigation-actions.json maps original callback/page identifiers to the local target and current control. Allowed cases click the actual link and require exact destination, HTTP200 and meaningful content: seeded cargo list data, booking/lookup form controls, exact About heading, or live socket plus seeded cargo data. Native login principal and role are verified before authenticated cases.

Anonymous cases click exposed public links for Cargo list, Track cargo and Live tracking. Hidden booking/protected-About controls are checked absent, then direct browser navigation exercises their target. Reader booking is likewise absent and direct navigation must return403. Anonymous protected navigation must return303 to the configured local login with no protected payload. Public About is clicked by all actors and its anonymous response is inspected for cargo markers.

The browser records the navigation request's original response across redirects. Generated Faces links carry a jfwid client-window parameter; only that single nonempty parameter (or no query) is allowed, while the origin and path remain exact. Other or duplicate query parameters are rejected. Window values are not published. Python validates all24 proofs, exact driver/source/target, native identities, denial status and required destination content before updating any observations. Canonical adapter matching rejects altered callback, source, source line, page, method, path, actor, write flag or session state. Missing/incomplete proofs cannot partially promote the catalogue.

Run from WSL:

    python3 tests/security/run_candidate_contracts.py --live-subset --output .work/kan15-navigation/catalogue-results.json

## Limits

These are read-only navigation proofs. No write callback or action-session case is promoted. Existing valid/invalid booking, routing, handling, tracking and socket workflows run in the same fresh fixture, but are not silently counted as proof for other action definitions. Full KAN-15 acceptance remains incomplete. A native exit2 means unsupported contracts remain, even when this increment passes.

Runtime results and exact reviewed inputs are retained under notes/evidence/kan-15-navigation-actions, with the separate review record under notes/agent-reviews. No production deployment, role-policy change or mutation of historical/synced sources is included.

## Verified result — 2 November 2026

Fresh execution passed 367 application and 417 Chromium checks, 35 reported domain cases (one inherited empty TODO), and 60 tooling checks. All24 navigation proofs passed; catalogue280PASS/222BLOCKED, native exit2. Task app/browser/network/private files were removed. Remaining222 contracts comprise156actions,20action-session and46internal/worker definitions. Independent review must be recorded before publication.
