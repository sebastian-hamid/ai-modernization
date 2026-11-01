# KAN-15 local identity/session foundation — work in progress

The original foundation increment was verified separately from Cargo Tracker. A subsequent [real candidate bootstrap](../cargotracker/README.md) now integrates login/session and monitoring/handling HTTP roles; full application integration remains incomplete. KAN-15 is In Progress, not accepted or complete. The historical application remains insecure and unchanged. The 502 KAN-14 candidate cases remain BLOCKED; integration-fixture success does not change their outcomes.

## Implemented components

- LocalLoginServlet authenticates using Servlet request.login against WildFly ApplicationRealm, rather than comparing application-stored passwords. A random session-bound CSRF token is required for login, and successful authentication rotates the session ID and token. Generic 401 responses avoid credential disclosure; no redirect supplied by a client is accepted.
- LocalLogoutServlet requires identity and CSRF, calls container logout and invalidates the session. GET is not a logout operation.
- AccessFilter reads a deployment-local exact-path tab-separated manifest from WEB-INF/access-routes.tsv. PUBLIC is explicit; otherwise at least one named role is required. Unknown and ambiguous paths are denied before downstream code. Anonymous API-style paths return 401; protected .xhtml paths redirect to the fixed login route; wrong roles return 403. Non-safe methods require CSRF; protected responses are no-store.
- RequiresRoles and RoleInterceptor enforce role checks at intercepted CDI method boundaries using container principal/role evidence. Empty roles and missing request context deny. Invoke through CDI proxies, not self-invocation or manually constructed objects; this is not an authorization mechanism for background workers.
- SessionTokens generates cryptographically random tokens and compares submitted values without ordinary string equality. A token must come from the same live session.

The test deployment configures cookie-only tracking, HttpOnly cookies and one-minute idle expiry. It uses ephemeral properties-realm digests generated outside the image. HTTP is limited to loopback in this disposable fixture; HTTPS/Secure/SameSite cookie configuration, login rate limiting and operational account management are not established by these tests.

## Actual runtime evidence

Run from WSL repository root:

    python3 tests/security-runtime/run_security.py
    python3 -m unittest discover -s tests/security-runtime -p test_harness.py -v

The harness builds only copied library/fixture inputs in ignored .work/kan15/context, uses the pinned KAN-13 Java/WildFly foundation, creates task-owned isolated runtime/credentials and removes them in finally. Existing task names/private files cause refusal; other services are not reused or removed. Sanitized results are recorded under notes/evidence/kan-15-security-foundation; raw logs remain ignored. The final run verifies 49 runtime checks plus three cleanup regressions, including Docker log/removal failure. The fixture has a small in-memory mutation counter solely to verify HTTP/CDI denial order. This counter is not an independent database/JMS/audit observer.

## Integration blockers and next work

1. A limited real Cargo Tracker bootstrap now exists in candidate/cargotracker (KAN-18 overlap); complete the remaining platform and workflow integration before full acceptance. Source inspection confirms Java EE javax APIs, GlassFish/Jersey registration, Derby/JMS resources and PrimeFaces 5.2 bindings; a modern-server capability WAR alone cannot run that application. Preserve original source and shared GlassFish.
2. Bind every KAN-12 page, API, safe asset and direct/AJAX callback to reviewed permissions. Exact route checks cannot authorize callbacks on mixed Reader/Operator pages. Apply method guards to real business actions/services and EJB roles where appropriate; do not treat hiding controls as enforcement. Adapt denial responses deliberately.
3. Keep worker identities, broker/filesystem ACLs, scoped internal routing, controlled import and deployment/migration authority separate from human roles. This request-bound CDI guard must not be used to invent human authority for MDB/batch execution.
4. Add WebSocket identity/Origin validation and close live sockets on logout/expiry; no post-revocation data. These controls are not implemented by a servlet filter alone.
5. Wire real KAN-14 browser/session adapters and fixture-scoped database, cumulative queue and business-audit observers. Verify authorized booking/routing/destination/handling/import workflows and denied mutations. Then rerun the 502 definitions plus detailed scenario expansions. No acceptance waiver is inferred.

Functional change verified here: fixture users can authenticate and exercise their assigned capabilities, while logout/expiry revoke subsequent fixture requests. Architecture: reusable servlet/CDI guards rely on WildFly-managed identity; the test WAR is separate from production library. Technical integration instructions above remain requirements, not deployed Cargo Tracker behavior.

Official references checked 1 November 2026: [WildFly 42 Elytron](https://docs.wildfly.org/42/WildFly_Elytron_Security.html), [Servlet 6.1 API](https://jakarta.ee/specifications/servlet/6.1/).
