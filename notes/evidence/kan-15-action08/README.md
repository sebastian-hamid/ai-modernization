# KAN-15 ACTION-08 retired-entry evidence

## Scope

ACTION-08 is the historical destination-dialog Cancel callback. The legacy source was recovered from the nested Cargo Tracker repository at commit `57fc7b32d2597e43b5e0d454e707e0146de5258a`; its source and historical WAR page hashes match at `a8872c4de0279a27f14a0ec3f8827efdd576f1d0ad64e261a049544c5b981118`. The legacy component ID is `j_idt8:j_idt23`, with source parameter `javax.faces.source`.

## Verified behavior

The unused candidate ChangeDestinationDialog bean was removed, so the old cancel() callback implementation is absent from the candidate build. A fresh owned runtime run posted that historical source ID to the current route using the current Jakarta Faces form and actor credentials where applicable. Operator and Administrator had a fresh authorized form, CSRF token, and ViewState; the actual response URL/status matched the current route and successful response, and its partial response contained no dialog close callback. Reader received 403; anonymous received configured-login 303. All four cases had unchanged SQL, queue, and business-invocation observations. The replacement cancellation checks passed for all four actors, including unchanged persisted cargo and denied-write effects.

The existing fresh runtime validation artifact is [validation.json](validation.json). It records the four actor proofs and fresh-run provenance. The native runner passed 696 checks and the Chromium suite passed 841 checks; private files were removed. Docker container and network checks found no owned `kan19` or `action08` resources after completion.

## Validation and limits

- `python3 -m unittest discover -s tests/security -p test_current_capabilities.py`: 27 passed.
- `python3 -m unittest discover -s tests/browser-workflows -p test_*.py`: 30 passed.
- The effects-bridge focused suite: 7 passed, including the new allowlist regression. The full browser harness suite passed30 tests.
- `git diff --check`: clean.
- Live capability counts: 424 PASS / 46 BLOCKED; retirements: 76 BLOCKED. Gate exit 2 is expected while other current cases and independent retirement review remain open.
- ACTION-08 is evidence-verified but not classified RETIRED or PASS until independent review. KAN-15 remains In Progress.

No shared baseline, Jenkins instance, or synced `sources/` content was changed.

The invoking PowerShell/WSL session surfaced process exit code 1 for the nonzero gate result; the canonical Linux report records `gate_exit: 2`. Browser workflow status was PASS.

## Attempts

An initial browser integration attempt reached696 native checks, then failed because the strict effects-stage allowlist omitted retired-action; private files were removed. After correcting the allowlist, one run passed696 native checks and841 browser checks. The first run after the callback-removal proof changes stopped before ACTION-08 at an isolated handling-voyage observer timeout after427 browser checks. It cleaned up; one bounded rerun then passed696 native checks and841 browser checks. No further retries were made.
