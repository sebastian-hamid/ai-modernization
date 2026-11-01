# Candidate tracking and legacy navigation (KAN-20)

## Functional behavior

The public home page links to the current authenticated workflows. Tracking remains restricted to Reader, Operator and Administrator, including the historical URL under /public/. /admin/track.xhtml without an ID displays a lookup form. A valid known ID opens persisted cargo details. Form input that is malformed or unknown displays a controlled message. A malformed or unknown ID in a direct GET returns404; missing IDs on details, destination change or route selection return404. No destinationCoordinates property or external map client is needed for tracking.

Historical GET entry points redirect303 to fixed local destinations:

| Historical path | Current destination | Roles |
| --- | --- | --- |
| /public/track.xhtml | /admin/track.xhtml (optional trackingId retained) | Reader, Operator, Administrator |
| /admin/map.xhtml, /admin/mapFrame.html | /admin/live.xhtml | Reader, Operator, Administrator |
| /admin/selectItinerary.xhtml | /admin/route.xhtml (trackingId required) | Operator, Administrator |
| /eventLogger/eventLogger.xhtml, /eventLogger/root.xhtml | /mobile.xhtml | Operator, Administrator |
| /booking/booking.xhtml, /booking/booking-date.xhtml, /booking/booking-destination.xhtml | /admin/book.xhtml | Operator, Administrator |

The old event logger and booking flow URLs start the current standalone form; partial flow state is not reconstructed. Retired POST callbacks never replay actions: authenticated permitted callers need CSRF first and then receive405. Readers receive403 for mutation entry points even when their query input is invalid. Anonymous callers go to fixed login before cargo lookup. Existing history in an old browser flow may require starting again.

## Architecture and technical details

LegacyNavigationServlet has exact URL mappings, which take precedence over Faces *.xhtml and static-file handling. This prevents obsolete raw map HTML and FlowScoped expressions from being rendered. The exact access manifest applies the same roles as the current destinations before servlet dispatch. AccessFilter treats protected .html navigation like .xhtml when redirecting anonymous callers.

Redirects use only fixed context-relative destinations. IDs retained on legacy links must be a single trackingId matching [A-Z0-9]{6,8}; arbitrary redirect parameters are ignored. The target view performs actual existence lookup. GET tracking lookup and form submission use CargoPages and the existing transactional facade. Roles and non-safe-method CSRF checks remain server-side, independent of visible links.

Some obsolete source templates remain in the candidate for provenance; these named entry points are intercepted. Unlisted routes remain deny-by-default. Historical sources and the historical running application are preserved. This change does not enable every original UI/API, alter handling/booking business rules, or complete full security/effect-observer acceptance.

## Verification

Run from WSL repository root:

    python3 tests/browser-workflows/run_browser.py
    python3 -m unittest discover -s tests/browser-workflows -p test_browser_harness.py -v
    python3 -m unittest discover -s tests/candidate-runtime -p test_harness.py -v

The disposable pinned WildFly/Chromium fixture exercises actual tracking form lookup, valid legacy navigation, malformed/unknown/missing and duplicate IDs, role checks before validation, fixed redirects and retired callbacks. Prior booking/destination/routing/mobile/live/session-expiry workflows remain in the same regression run. Sanitized final evidence and exact input hashes are recorded under notes/evidence/kan-20-navigation; independent review is recorded separately under notes/agent-reviews. HTTP denial does not establish independent database/queue/audit absence.
