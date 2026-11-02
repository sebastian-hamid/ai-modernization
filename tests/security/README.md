# KAN-14 desired access contracts

These are candidate requirements, separate from historical characterization. Default execution remains non-live and BLOCKED. The optional fresh live subset below establishes only its explicitly bound cases; original historical records are preserved.

## Run from WSL repository root

    python3 tests/security/generate_cases.py
    python3 -m unittest discover -s tests/security -p test_contract_engine.py -v
    python3 tests/security/run_candidate_contracts.py
    python3 tests/security/probe_legacy_gaps.py

The generator derives 502 actor/surface/session cases from the approved KAN-12 inventory. The 16 unit cases check the assertion engine with artificial observations; they are not application security tests. The default candidate command reports all 502 BLOCKED and exits2. The optional --live-subset executes the real isolated runtime for four bindings and keeps the other498 BLOCKED. Expand real application/browser/service adapters in KAN-15; do not swap in mock observations to obtain green results.

The legacy probe creates a new container from the recorded historical image ID, binds a Docker-assigned loopback port, uses fresh seeded data, submits one handling event, closes its WebSocket and removes only its created container ID in finally. Docker rejects an existing name. It cannot accept a shared URL. Its expected exit is 1: eight desired-security failures and two public-page successes. Missing image, readiness failure or request errors are infrastructure errors, not authorization passes. Logs and full observations remain ignored under .work/kan14; sanitized summary lives under notes/evidence/kan-14-security.

## Adapter contract and required assertions

Each case has a stable surface/actor/session ID and expected allow/deny. Page and callback bindings come from the source inventory; adapters must resolve templates, JSF flows and AJAX ViewState using real rendered pages. A source expression alone is not a successful action. Use existing valid fixtures first, then invalid IDs/inputs and direct replay; malformed-input rejection cannot stand in for authorization.

- Verify a real authenticated server principal and assigned role for both allowed and denied role cases. Use distinct Reader, Operator and Administrator fixtures; no role claims supplied in request payloads. Anonymous requests carry no cookie/Authorization. Public landing/About remain reachable; operational tracking, cargo and map data require identity.
- Anonymous APIs return 401, insufficient roles 403, never login HTML/500. Protected pages may return 401 or navigate via 302/303 to the configured login, with no operational payload. Arbitrary redirects, flow navigation, hidden buttons and HTTP 200 alone do not demonstrate authorization.
- Exercise every callback directly, including JSF AJAX replay from Reader against Operator actions. Reader can read; Operator can book/reroute/change destination/report; Administrator additionally controls imports. Verify actual business outcomes for allowed actions and meaningful payload/render checks for reads.
- For logout/expiry, log in successfully, capture authenticated identity, perform real logout or server expiry, verify revocation, then replay saved page/action/API credentials. Catalogue includes protected pages, interfaces and mutating callbacks. New unauthenticated requests alone are insufficient.
- Denied writes require independent fixture-scoped database records/events, cumulative enqueue/consume/retry/dead-letter counters and business invocation audit before/after. Wait for correlated workers to settle; nonempty snapshots must match exactly. Queue depth alone can miss enqueue-then-consume; counts alone can miss replacement updates, so include record content hashes/IDs. Security-denial audit events may increase separately. Missing observers or unresolved retry disposition are BLOCKED.
- Allowed mutations require actual verified effects. WebSocket success requires authorized message delivery, not just 101; authenticated wrong-Origin denial, session revocation/disconnect and no post-revocation data are required. Origin cases have separate IDs; full socket lifecycle adapters remain pending.
- Human application roles confer no broker/filesystem/server/deployment administration. Background control-plane cases and scoped machine cases are distinct; BG-06 uses deployment/migration identity, not an application worker. Migration should preserve existing data and disable destructive startup reseeding. The routing service gets only its scoped capability; do not use Administrator credentials for internal HTTP.
- Adapters must additionally expand aggregate service groups into each named method and cover safe static allowlists, resource bypass, flow descriptors, CSRF/missing tokens, invalid/unknown IDs, role tampering, cross-role replay, stale ViewState and worker ACL/replay/restart scenarios. The 502 definitions enumerate actor/surface/session combinations, not exhaustive scenario implementations. Existing malformed-input characterization remains useful but is not candidate access verification.

Observations use supported, status, protected_payload_absent, identity (server_verified/principal/roles), semantic_success, authorized_effect_verified and, where relevant, effects, revocation and WebSocket fields. Machine cases require machine_identity_verified and the exact required_machine_scope. These fields are assertions backed by real adapter evidence, never trusted client declarations. Engine run_cases catches unsupported adapters as BLOCKED and other exceptions as ERROR without exposing exception text. Exit 0 requires a nonempty all-PASS run; any FAIL/ERROR exits 1; any BLOCKED exits 2. Persist sanitized case IDs/outcomes, not cookies, credentials, session IDs or sensitive response bodies.

## Recorded result and limits

See notes/evidence/kan-14-security/validation.json and notes/agent-reviews/2026-11-01-kan14-review.md. The live probe reproduces anonymous operational reads, handling mutation and cross-origin upgrade. Its monitor observation proves a positive mutation, but does not prove queue/database/audit absence for a denied write. At that original checkpoint, real candidate identities, browser workflows, logout/expiry, independent effect observers and machine ACLs were blocked on subsequent implementation. Later increments establish bounded real coverage as described below; full acceptance remains incomplete. The KAN-13 capability spike is not Cargo Tracker and cannot satisfy these cases. Jenkins baseline remains historical characterization; this red suite is deliberately not silently added as a passing stage.


## Subsequent scoped effects evidence

The [disposable independent effects observer](../../docs/candidate/independent-effects.md) now verifies selected real handling/forged-booking denials and Operator logout/idle-expiry replay, with an allowed processing control. This supersedes the blanket observer-unavailable statement for that bounded subset only. The optional --live-subset command launches a fresh candidate and binds four real handling-denial/revocation cases; the remaining498 cases stay BLOCKED and exit 2. Default execution remains all 502 BLOCKED. Missing adapters and remaining machine/worker/retry scenarios are not converted to PASS.


## Monitoring and private-template binding follow-up

The [read-access binding follow-up](../../docs/candidate/read-access-bindings.md) expands the optional live adapter to16 definitions; other486 remain BLOCKED/exit 2. Earlier4PASS/498BLOCKED statements describe the first effects increment. This adds parsed monitoring semantics and exact private-template denials, without application or permission changes.


## Complete HTTP API definition binding follow-up

The [API access matrix](../../docs/candidate/api-access-matrix.md) binds all 27 API definitions (active roles, human logout/expiry and scoped native routing) plus eight private templates and 20 private metadata/source-note cases: 55 bound, 447 unsupported/BLOCKED, overall exit 2. Earlier 4 PASS / 16 PASS counts are historical checkpoints. This remains a partial implementation of the entire 502-definition catalogue.


## Filtered cargo and About page bindings

The [read-view follow-up](../../docs/candidate/read-views.md) adds six page surfaces with native active roles and protected-page logout/expiry cases. The optional live adapter now binds 103 definitions, leaving 399 unsupported/BLOCKED and overall exit 2. Earlier 55/447 results remain historical evidence.


## All HTTP page definitions

The [HTTP page matrix](../../docs/candidate/http-page-matrix.md) binds all page GETs and their declared role/session cases, using specific content and fixed alias targets. Dynamic map allows require real browser data/socket proof. The optional live command now orchestrates the fresh browser/runtime wrapper: 243 bound definitions, 259 unsupported/BLOCKED, overall exit 2. Earlier counts remain historical checkpoints; callbacks, socket definitions and worker/internal boundaries remain incomplete.


## Structured socket definitions

The [socket matrix](../../docs/candidate/socket-access-matrix.md) adds all 13 socket role/origin/lifecycle definitions backed by real frames, saved-cookie replay and post-revocation witness delivery. The expected live subset is 256 definitions with 246 remaining unsupported/BLOCKED. Historical page-only 243/259 results remain preserved.
