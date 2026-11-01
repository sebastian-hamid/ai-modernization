# Candidate cargo browser workflows — KAN-19

1 November 2026. Limited increment, not full KAN-19 acceptance. The [routing extension](routing-workflow.md) now adds secured sample routing. Authenticated live tracking/WebSocket lifecycle and replacement of the legacy mobile event logger remain unimplemented. KAN-15/KAN-18/KAN-19 remain In Progress; KAN-14's complete desired-access adapter remains blocked.

## Functional behavior

- Reader, Operator and Administrator can open /admin/dashboard.xhtml, follow a tracking link to /admin/show.xhtml and see actual persisted cargo details.
- Operator and Administrator can use /admin/book.xhtml to choose existing origin/destination locations and a valid ISO calendar arrival date. Equal origin/destination, unknown choices, missing values and invalid calendar dates are rejected. No new future-date policy is introduced.
- Successful booking creates a real cargo through the existing booking service and redirects to its generated tracking ID. Operator/Administrator can open /admin/changeDestination.xhtml, choose an existing destination different from the origin, save and return to details. A separate Reader session sees the saved destination.
- Reader has no mutation navigation controls. Server checks also deny direct mutation links and forged POSTs with a legitimate Reader CSRF token. Anonymous protected-page navigation goes to fixed login. Missing/invalid/unknown tracking IDs return controlled404 after authentication, rather than uncontrolled500.
- Details fit the tested390px mobile viewport; this is responsive coverage for these pages, not acceptance of all mobile flows or devices.

## Architecture and policy

The new pages use Faces4.1 templating and PrimeFaces16 full-submit command buttons; browser JavaScript and requested assets are exercised. CargoPages is a view-scoped presentation bean; business work stays in BookingServiceFacade and BookingService.

An HTTP exact-path manifest enforces Reader/Operator/Administrator reads and Operator/Administrator mutation pages. Non-safe requests require the real session CSRF token. Facade mutation methods additionally require Operator/Administrator via the reviewed CDI interceptor; the EJB booking service is role-restricted independently of control visibility. Read facade methods permit all three roles.

The transactional facade encloses repository queries and DTO assembly. Real browser testing exposed Hibernate lazy collection access outside a transaction; this correction avoids keeping a persistence session open through rendering.

Cargo construction now creates a distinct empty itinerary per aggregate, avoiding shared orphan-delete collection ownership. Delivery determines NOT_ROUTED from empty value state rather than static singleton identity. Original three routing-status assertions remain; assigned good/bad test fixtures now contain real legs, and a new non-singleton empty regression explicitly verifies NOT_ROUTED. The original synthetic empty assigned-route fixtures conflicted with this correction; the independent reviewer identified that conflict before final acceptance.

Public static resource permissions are exact file/library pairs in ResourcePolicyFilter plus exact manifest paths, limited to known Faces/PrimeFaces scripts/CSS/font. Only GET/HEAD and ln/v parameters are allowed; unknown/dynamic resource names and pfdrid attempts deny404. This is not a blanket resource prefix exemption. Other unported UI and API surfaces remain disabled.

## Technical verification

From WSL repository root:

    python3 tests/browser-workflows/run_browser.py
    python3 -m unittest discover -s tests/browser-workflows -p test_browser_harness.py -v
    python3 -m unittest discover -s tests/candidate-runtime -p test_harness.py -v

The wrapper runs the actual candidate harness with a browser callback. Application runtime is the pinned disposable KAN-18 image build (fresh selected-input context, H2 only for lab, explicit opt-in); it is removed afterward. Browser tooling is Playwright1.64.1 with npm lock plus official immutable Microsoft image47b510dd..., running Chromium on a task-owned internal network. No host Node/browser installation is needed. The browser build context permits only Dockerfile/package/lock/workflow script.

Credentials go over stdin to private tmpfs. Browser storage state, cookies, traces, form HTML and credentials are not published. Sanitized results are read while the browser container is running, then container/network are removed. Logs remain ignored. The first harness used docker cp on a tmpfs path and failed report collection; corrected to docker exec while running. Failure/timeout/removal tests check cleanup and false-success handling.

Initial booking/destination increment final run:30 real browser assertions pass;35 application runtime checks pass;35 domain cases pass (one inherited empty TODO);3 browser and3 application mocked cleanup regressions pass. Browser report has no page/resource errors. Evidence is under notes/evidence/kan-19-browser. This is Chromium-only verification; Firefox/WebKit and exhaustive accessibility/concurrency/restart/session-expiry behavior are not established here.

The browser validates actual new cargo creation and destination readback in another authenticated session. Denied mutation checks establish HTTP denial; independent database/queue/business-audit absence remains unverified. Full KAN-14 results are not silently converted to PASS. Historical GlassFish/Jenkins/source and synced references remain unchanged.

References checked: [Faces4.1 metadata placement](https://jakarta.ee/specifications/faces/4.1/vdldoc/f/metadata.html), [Playwright Docker](https://playwright.dev/docs/docker).


## Subsequent live UI increment

The authenticated [live tracking view](live-tracking-ui.md) now provides actual rows/markers and session-end clearing. Earlier disabled-map/live-UI statements are historical; the raw legacy map client remains blocked. KAN-19 still requires the mobile event logger. KAN-17 endpoint work is Done in Jira.
