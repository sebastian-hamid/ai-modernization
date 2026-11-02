# Structured socket access matrix (KAN-15)

## Verified scenarios and binding requirements

The browser-backed gate binds the thirteen socket definitions: three native-role allows with actual authorized frames, anonymous401, three authenticated wrong-Origin403 denials, and logout plus idle expiry for each of Reader/Operator/Administrator. Together with 243 HTTP/API/private definitions the expected bound total is 256; other 246 remain unsupported/BLOCKED and overall exit 2.

Native role identity comes from the actual server /session response after login, not client-provided role fields. A successful browser WebSocket OPEN and real DEF789 event establish an authorized subscription;101 is inferred from the successful WebSocket upgrade, not accepted as an allow on handshake alone. The protocol's send evidence is the server's onCargoInspected data frame, not a new client mutation command.

Each session case begins with authenticated identity and actual authorized data. JSESSIONID is captured before revocation into a private in-memory variable. After real logout or at least 75 seconds without HTTP traffic, the existing socket must close. A separate cookie-less API client explicitly replays the saved cookie to /session and a valid-origin upgrade URL; both must return401, with no fixture payload on upgrade denial. A newly anonymous request is insufficient.

No new frames may arrive on the closed socket after a later real handling event. A still-authorized independent witness receives that event, preventing a false pass caused by a broken producer. Each independent window starts a fresh witness transport on the same verified native Administrator session; it must receive pre-revocation data, at least six matching frames and the final idle-window location state, then a new matching post-revocation frame while still OPEN. Counts and alternating locations are not unique event IDs under hypothetical duplicates. Producer requests explicitly carry that original saved session cookie. Reader/Admin expiry sessions receive only WebSocket traffic during their idle window; the independent Admin producer's HTTP activity does not refresh their sessions. Different browser contexts separate concurrent sessions even when usernames match.

Existing Reader logout and Operator expiry cases are retained. Four additional identities cover Reader expiry, Operator logout and both Administrator states, with pre-revocation delivery and a second actual idle window. Browser command timeout is 300 seconds to accommodate both idle windows; the user's overall task deadline remains separate.

## Fail-closed reporting

The Node runner publishes exactly thirteen sanitized socket observations. The wrapper validates the entire set before updating any access observation: expected native principal/role, status, payload absence, actual opened/data-bearing socket, and complete old-cookie/closure/no-frame revocation evidence. Missing, extra or inconsistent proofs fail the fixture rather than promote a partial set.

Saved cookies, CSRF and passwords are never serialized or placed in command arguments. Anonymous upgrade checks use an independent API request context with no cookie or Authorization header. Wrong-Origin checks deliberately retain a valid native session. The API request context is disposed and owned browser/network/app/private files follow existing cleanup.

The adapter binds only the approved canonical WS path/method/origin/session metadata. It does not treat scattered historical passing assertions or arbitrary archived summaries as fresh observations.

## Reproduction and limits

    python3 tests/security/run_candidate_contracts.py --live-subset
    python3 -m unittest discover -s tests/browser-workflows -p 'test_*.py' -v

Final actual counts and exact hashes are in notes/evidence/kan-15-socket-matrix; independent review is recorded separately. All existing page/form/routing/mobile/claim/live tests run in the same fresh fixture.

Observation windows are bounded; a frame already queued before revocation is not a guarantee of zero in-flight data. Current tests wait for closure, then compare counts across later distinct events. They do not establish every malformed frame, abrupt network failure, concurrency, restart or production broker/filesystem boundary. Remaining 246 definitions are 180 actions,20 action-session cases and 46 internal/worker cases. Full KAN-15 remains incomplete; H2/Chromium and one inherited empty domain TODO limits remain.


## Witness failure diagnosis

The earlier extended test reused its first-window witness. Sanitized diagnostics showed that raw socket closing abnormally with1006 at90,057ms, after nine frames, while every producer HTTP identity check still passed. It was open immediately after the other Administrator session's logout; the evidence does not establish logout as the cause. The pinned HttpSessionImpl last-access getter delegates directly to the underlying session, weakening the initial cached-wrapper explanation.

The test correction uses a new verified positive-control transport for the second75-second window instead of waiting on an already closed control. It preserves all target expiry/logout, old-cookie replay and no-frame assertions, and strengthens exact witness event progression. No server, timeout or application security behavior is changed. The cause of the longer-lived abnormal closure remains unconfirmed; this increment does not claim long-lived transport availability is fixed. Failure/diagnostic artifacts are retained separately.
