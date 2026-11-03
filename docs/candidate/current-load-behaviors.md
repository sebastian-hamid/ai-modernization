# Current destination-form and cargo-details loads

KAN-15, 3 November 2026. This increment implements ACTION-07 and ACTION-20 as the approved current GET equivalents. It preserves all 502 historical definitions and keeps their callback results separate.

## Functional coverage

For all four actors, the fixture directly requests a selected cargo's destination editor and details page. Reader can read details but cannot edit destinations. Operator and Administrator can load both. Anonymous requests must use fixed local login redirects without cargo payload.

Allowed editor loads must select the current destination, not merely include that destination among available options. Details must show the exact tracking ID, origin and destination display names, routing/transport status and the known fixture deadline. An independent Reader API snapshot supplies the expected cargo values. The load stage runs after the Operator cargo changes to USNYC and before the Administrator control changes from FIHEL, so accidentally loading the other cargo cannot satisfy the destination assertion.

Every actor also requests each page with a missing, malformed and unknown tracking ID. Allowed roles receive sanitized 404 results; anonymous/insufficient-role requests remain denied before cargo lookup. The fixture compares settled independent database/queue/business-invocation snapshots around all read requests.

## Adapter and policy boundary

The manifest explicitly moves only these two already-approved behavior rows to mapped status; all role and retirement rules remain intact. Code pins the updated partition. Fresh native current observations are kept in a separate map from historical observations; generic historical callback evidence cannot satisfy these drivers. The current adapter requires exact canonical contracts, a fresh owned-run receipt, strict role/principal identity, source/query/target binding and explicit selected-value/invalid-input evidence.

Two integration attempts stopped at the details location-name assertion and cleaned up their owned resources. The first comparison expected raw names; an assembler-only diagnosis then incorrectly expected names plus UNLOCODEs. Field-only diagnostics isolated Origin and Destination. Inspection of the complete template/getter chain and a bounded no-network diagnostic using compiled candidate classes established that the page name getters remove the code but retain a trailing space. The corrected oracle trims surrounding whitespace only for the two visible location names and compares exact independent API names. IDs, statuses, deadline and selected destination code remain strict; wrong names and unexpected code-bearing display values fail. Both failed native reports are retained privately; their response bodies were not captured.

## Verification

The final corrected fresh fixture reports **332 PASS / 138 BLOCKED across 470 current cases**: exactly eight new current load cases pass. The historical 502-case audit remains **324 PASS / 178 BLOCKED**, and all **76 retirement checks remain BLOCKED**. Gate exit is 2; full acceptance is incomplete.

Native 603 and Chromium 431 checks passed; 36 fixture and 56 security unit tests passed. All owned containers, private network and credential files were removed without errors; shared historical Cargo Tracker, Jenkins and baseline-agent containers remain running. The 24 invalid-input checks passed. The grouped read-effects comparison passed, but raw semantic HTML and grouped snapshots are not separately serialized; independent review can inspect driver logic and recorded results rather than re-evaluate those private HTML/group samples.

See [sanitized evidence](../../notes/evidence/kan-15-current-loads/validation.json) and [review record](../../notes/agent-reviews/2026-11-03-kan15-current-loads-review.json). Remaining current blocks: 48 pending behavior cases, 44 replacement capability cases and 46 internal/service/worker cases. All retirement checks remain unsupported.
