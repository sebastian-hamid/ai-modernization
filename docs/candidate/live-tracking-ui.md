# KAN-19 live cargo tracking UI

1 November 2026. /admin/live.xhtml is available to Reader, Operator and Administrator. It replaces use of the blocked legacy map client with local JavaScript, a port-coordinate SVG plot and a complete cargo table; no external CDN/map-key service is used. The old mapFrame.html remains blocked. This is an approximate port plot, not cartographic route navigation: unreceived cargo uses origin coordinates, unknown locations have no marker, and overlapping port markers are listed separately in the table.

The browser opens the reviewed session-bound WebSocket, then fetches the initial authenticated cargo snapshot. Actual cargo-inspection/handling events update rows and markers without reloading the page or issuing automated HTTP keepalive requests. Reconnect explicitly reloads the snapshot, including newly booked/rerouted cargo which has not emitted an inspection event. This is an event-driven view, not a transactional database change stream or guarantee that all booking actions are pushed immediately.

Snapshot and socket messages now share complete cargo fields. REST origin/lastKnownLocation codes remain unchanged. Original socket origin/destination/lastKnownLocation name semantics are preserved, with explicit Code and Name fields added for the UI. updatedAt is the delivery calculation timestamp; older snapshots cannot overwrite newer events, and socket data takes precedence over an equal-time initial snapshot. Millisecond timestamps do not guarantee a total order for concurrent equal-time events; no monotonic stream revision or race-free concurrency claim is made.

Data is rendered with textContent and encoded detail links, not HTML string interpolation. The UI tracks connection generations, aborts outstanding reads and ignores results from obsolete connections. Logout/HTTP idle expiry closes sockets via KAN-17; the live page removes all cargo rows/markers and prompts sign-in. Disconnection also clears stale operational data; reconnect is manual. No browser storage, periodic polling or automatic reauthentication is added. Previously delivered/queued frames and browser memory cannot be retroactively erased.

Verification uses the real candidate and actual JMS-derived events for all three roles. Tests check Operator/Administrator initial snapshots/markers, Reader delayed-snapshot merge, Stockholm marker movement and row text, legacy socket-name compatibility, deliberately delayed old REST response after a newer event, logout/expiry DOM clearing, and an authorized Administrator receiving a post-expiry event while revoked views remain empty. Live pages have their own error/resource listeners. Plain-HTTP lab hosts use crypto.getRandomValues for the nonsecret UUID correlation rather than secure-context-only randomUUID.

Run python3 tests/browser-workflows/run_browser.py. Exact counts/hashes and cleanup are in notes/evidence/kan-19-live/validation.json; underlying35 domain cases retain one inherited empty TODO. Seven mocked harness cleanup regressions remain separate from product coverage. Shared historical services/source are unchanged.

KAN-19 remains In Progress for the legacy mobile event logger; full KAN-15/KAN-18 and independent KAN-14 database/queue/audit absence remain open. KAN-17 endpoint acceptance is Done; it does not imply the old map client was ported.

## Subsequent mobile workflow increment

The [responsive handling form](mobile-handling.md) now replaces the legacy mobile flow for supported handling work. Earlier mobile-disabled/pending statements describe prior checkpoints. Full platform/security/resilience acceptance remains separate.
