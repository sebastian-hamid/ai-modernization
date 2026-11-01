# Fresh monitoring and private-template bindings (KAN-15)

This follow-up extends the live catalogue adapter without changing application sources or permissions. Reader, Operator and Administrator monitoring reads must return the four actual seeded cargo IDs in parsed JSON; anonymous monitoring must return401 without fixture cargo markers. Server principal/roles come from the real authenticated session.

Direct GETs to the two inventoried WEB-INF templates must return404 without fixture cargo markers for anonymous and all three human roles. The adapter accepts only the exact inventory paths, GET method and internal-template classification. It cannot reuse these observations for an operational page. The existing oracle permits controlled403/404 for these private resources; success and login redirects are rejected.

The adapter now binds16 definitions: API-01 four active actor cases, PAGE-01/PAGE-02 eight active actor cases, and the four previously verified API-02 handling-denial/revocation cases. Other486 definitions remain unsupported/BLOCKED; the full gate must exit2. Previously recorded4PASS/498BLOCKED evidence is preserved as the first increment.

Run python3 tests/security/run_candidate_contracts.py --live-subset from WSL repo root. It creates a fresh opt-in disposable fixture; archived reports are never treated as a fresh run. The grouped GET/HEAD monitoring cases exercise both methods: GET requires actual JSON semantics (or anonymous denial without cargo markers), and HEAD requires200 for each native role or401 for anonymous with an empty body.

Final sanitized results and hashes are in notes/evidence/kan-15-read-bindings; review record is separate. Existing observer/denial/positive-processing/session checks run again. No browser-script or application change is included, so the prior210-case Chromium result in notes/evidence/kan-15-effects remains a historical regression result, not a rerun for these binding-only changes. One inherited domain test is empty. Marker inspection is bounded and does not prove every possible payload is secret-free.
