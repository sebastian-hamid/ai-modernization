# KAN-17 session-bound tracking WebSocket

1 November 2026. Endpoint security increment; the old map client remains disabled and unported. Do not claim a working live-map UI. KAN-19 UI work and full candidate acceptance remain open.

The exact /tracking endpoint requires a native authenticated Reader/Operator/Administrator cookie session and a single Origin matching cargo.websocket.allowed-origins. Default origins are empty, so missing configuration denies access. A nonsecret UUID connection query correlates the authorized upgrade to its server-side HttpSession; no credentials/session identifiers are placed in the URL. The filter reserves a bounded short-lived binding; onOpen consumes it and verifies the native principal again. Shared endpoint configuration is not used to store per-user state.

SocketSessions owns pending/active connections, checks HTTP idle validity before publishing, and uses a managed one-second expiration task. An HttpSession listener revokes connections on invalidation/logout. Invalid sessions close with policy code1008; no new events are sent after revocation/closure. Frames already queued before closure can still arrive in transit; this is not a guarantee to retract previously authorized data. Failed asynchronous sends close/remove that connection without throwing into the handling transaction.

Normal Maven deployment defaults to15-minute HTTP sessions. The disposable test build sets the session.timeout.minutes Maven property to1 and a single private Docker application origin; normal deployments must explicitly set their actual trusted origins. WebSocket traffic does not count as HTTP activity. Broker/tenant policy remains the approved shared organizational cargo view; no new tenant isolation claim.

Reproduce with python3 tests/browser-workflows/run_browser.py. Final evidence: notes/evidence/kan-17-socket. Actual47 application checks,35 domain cases (one inherited empty TODO),89 browser checks pass. Cases include real JMS-derived frames for Reader/Operator/Administrator, HTTP401 anonymous upgrade,403 authenticated wrong-origin upgrades, logout closing an existing socket,75-second HTTP idle expiry despite traffic, and no additional frames observed after closure. App/browser/private network/private files were removed. Historical source/GlassFish/Jenkins preserved.

Missing/duplicate Origin, malformed correlation parameters and abrupt-disconnect recovery were reviewed in source but not separately exercised at runtime. Full independent database/queue/audit absence and complete KAN-14 adapters remain unverified. KAN-14 stays502BLOCKED; this ticket does not close KAN-15/KAN-18/KAN-19 or prove full production security.

The old admin/mapFrame.html constructs a socket without the new correlation query and stays blocked by the route manifest. Its migration is a subsequent UI task.


## Subsequent live UI increment

The authenticated [live tracking view](live-tracking-ui.md) now provides actual rows/markers and session-end clearing. Earlier disabled-map/live-UI statements are historical; the raw legacy map client remains blocked. KAN-19 still requires the mobile event logger. KAN-17 endpoint work is Done in Jira.
