# Complete HTTP page access bindings (KAN-15)

## Scope and functional behavior

The live subset binds all 25 inventoried page entry points and their permitted-role logout/expiry cases:100 active page cases and 96 page lifecycle cases. With 27 API and 20 private-resource definitions, this is 243 bound definitions. Other 259 remain unsupported/BLOCKED; full gate exit remains2. Page GET success is not proof that every callback or mutation is covered.

Known valid input is supplied before testing authorization. The fixture renders the real Operator booking form, submits its actual ViewState and session CSRF, and verifies a fixed details redirect containing a newly persisted tracking ID. That future-deadline cargo is used for detail, destination and route views, avoiding a false allow result based on malformed/unknown IDs or an expired sample deadline.

Allowed pages require specific content: complete dashboard IDs, exact cargo details, populated destination controls, actual candidate route tables/choice, real form CSRF/ViewState and control IDs, or the established filtered-list/public-page semantics. Legacy GET aliases must first return303 to their exact fixed local target, then the target must render meaningfully. Retired POST callbacks remain separate405 behavior, not successful mutation coverage.

Anonymous protected pages must return a fixed login303 with no fixture payload. Reader access to Operator pages must return403 before lookup/rendering. Saved authenticated cookies are replayed after actual logout and idle expiry for each role permitted by the approved inventory. These replays run within the existing settled independent-effect windows.

## Generic error-help pages

Direct /error.xhtml and /error_404.xhtml are public generic help pages, consistent with their approved sanitized-error classification. They contain fixed text and context-local Home/Sign in links, no JavaScript or external assets, no cargo data, exception/session/password text or query echo. Malicious message/next parameters are ignored.

These direct help-page GETs return 200. This change does not remap container error handling or replace the actual401/403/404 statuses of denied/missing requests. The initial Faces-component version failed the strict error-page semantic check; literal HTML replaced the unnecessary components before final verification.

## Browser-backed dynamic proof

A live-map HTML shell is insufficient. Runtime observations for native-role PAGE-09/PAGE-10 allows start unsupported until Chromium follows each alias and observes ABC123 plus Live socket state. Its role is verified from the actual server session response.

The browser wrapper requires exactly six sanitized proofs: two paths for Reader, Operator and Administrator. Each must match server-verified runtime identity, expected source/final paths, successful navigation, observed cargo and a live socket. Promotion is atomic after all proofs validate; missing/extra/mismatched proofs cannot turn HTML-only responses into PASS. No cookie, password, token or raw HTML is stored in proofs.

The optional live catalogue now invokes that fresh browser/runtime wrapper and requires browser checks and container/network cleanup. It returns the same runtime report after cleanup, then evaluates canonical contracts. It never imports archived PASS summaries as a fresh execution. Default non-live mode remains all-BLOCKED. Standalone runtime smoke execution lacks dynamic browser proof and is not complete page acceptance.

## Reproduction and evidence

From WSL repository root:

    python3 tests/security/run_candidate_contracts.py --live-subset
    python3 -m unittest discover -s tests/security -p 'test_*.py' -v
    python3 -m unittest discover -s tests/browser-workflows -p 'test_*.py' -v
    python3 -m unittest discover -s tests/candidate-runtime -p 'test_*.py' -v

Sanitized final reports and exact hashes are under notes/evidence/kan-15-all-pages; review is separate. All existing booking/routing/mobile/claim/live workflows execute in the browser run, with actual effects and prior observer/cleanup checks retained.

Remaining 259 definitions consist of 180 action cases,20 action-session cases,7 socket cases,6 socket-session cases and 46 internal/worker cases. Existing browser tests cover portions of socket behavior, but those definitions are not silently bound without structured adapter proof. Full worker/import/retry/restart and production security acceptance is incomplete; one inherited domain case is empty. H2/Chromium fixture evidence does not prove every input, browser or deployed environment. Historical sources/runtime and synced references remain untouched.
