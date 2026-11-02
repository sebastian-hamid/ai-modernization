# KAN-26 WebSocket disconnect regression

Scope: isolated candidate fix and regression. No production deployment is included.

## Functional behavior under test

A signed-in Administrator receives actual DEF789 data on a separate native WebSocket, then the client resets TCP without sending a WebSocket Close frame. A healthy, separately established browser witness must continue receiving events. A different, freshly booked cargo is then received at CNHKG: the healthy witness must see IN_PORT/CNHKG and a newly authenticated Reader must read that persisted state through REST in a separate transaction. The healthy witness finally requests close code 1000 and must observe a server close response with code 1000. This checks a normal close response, not exhaustive transport conformance.

## Architecture and technical execution

The regression uses the existing disposable WildFly/H2/Artemis fixture and private Chromium network. Generated native credentials travel only through stdin into tmpfs. The additional Node HTTP upgrade validates status 101 and Sec-WebSocket-Accept with the original authenticated session and allowed Origin, observes the expected actual cargo payload bytes, then calls resetAndDestroy. Payload matching is a limited application-data witness, not a general WebSocket frame parser. Browser delivery and independent REST readback assert structured cargo data.

Run from the WSL repository:

    python3 tests/security/run_candidate_contracts.py --live-subset --output .work/kan26/catalogue-results.json

The full access catalogue still returns exit 2 when unsupported cases remain. Do not interpret that as a passing complete security gate. Fixture cleanup and individual application/browser assertions must also pass.

## Candidate transport fix

A read-only management query on the disposable WildFly listener returned read-timeout 90000 ms, write-timeout 90000 ms and no-request-timeout 60000 ms. With no heartbeat, the retained original browser connection closed abnormally with code 1006 after 90,055 ms despite receiving nine cargo frames and a still-valid Administrator HTTP session. These observations are retained as before evidence.

The candidate now submits an empty WebSocket PING every 25 seconds for a valid binding through the existing managed executor. Browser protocol PONG traffic addresses the listener's inbound inactivity timeout without making HTTP requests. One task per binding may be in flight. Control-frame I/O runs outside the binding monitor; errors revoke only that binding and submission rejection does not terminate the periodic expiry task. The existing one-second validity checks, logout revocation and HTTP expiry remain in place.

Fresh execution must show the original transport still OPEN beyond 90 seconds and at least fifteen actual cargo events, together with all-role logout/expiry, reset isolation, unrelated persisted cargo and normal close response. A passing result is bounded runtime evidence, not a guarantee for arbitrary slow/nonreading peers or managed-executor saturation.

## Investigation boundaries

The original first-window Admin transport remains open as an aging diagnostic subject while a fresh second-window transport controls access-policy checks. Sanitized evidence records its open/close timestamps, close code and received frame count. Before/after evidence distinguishes the reproduced listener-idle symptom from abrupt peer reset isolation. Neither proves that every possible stale-server-session race has been exercised.

Global listener timeouts, HTTP session lifetime, authorization rules and cargo business rules are unchanged. KAN-26 requires passing fresh evidence and independent review before completion. Historical and synced sources, shared Jenkins and the historical application are preserved.

Current execution results and independent review are recorded under notes/evidence/kan-26-disconnect and notes/agent-reviews.

## Verified result — 2 November 2026

Fresh integrated execution passed 367 application checks and 348 Chromium checks, with 35 reported domain cases (one inherited empty TODO). The original connection stayed OPEN for 152,127 ms and received fifteen cargo events; no close was observed. TCP reset isolation, unrelated cargo persistence, code-1000 close response and all-role logout/expiry passed. All 54 tooling checks passed independently. The catalogue remains 256 PASS / 246 BLOCKED, native exit 2; this is not full security acceptance. Task app/browser/network/private files were removed. See notes/evidence/kan-26-disconnect/validation.json and the separate review record.
