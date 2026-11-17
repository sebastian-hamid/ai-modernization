# KAN-15 rendered handling callback denial run

Date: 2026-11-17
Run scope: `kan15-handling-callback-retirement` isolated candidate/browser fixtures.

## Result

The corrected fresh runner completed successfully: 777 candidate checks and 958 browser checks passed. Its aggregate report records 470 current capability passes, 44 existing RETIRED observations, 32 remaining BLOCKED observations, and gate exit 2 because blockers remain.

The browser report contains all 20 actor/action callback combinations for ACTION-36, ACTION-37, ACTION-38, ACTION-39, and ACTION-42 (anonymous, Reader, Operator, Administrator):

- Anonymous submissions returned 303 to login.
- Reader submissions returned 403.
- Operator and Administrator submissions returned 405 because the legacy callback POST handler is absent.
- Protected payload was absent and independent database/queue effects were unchanged for all callback submissions.
- The replay is explicitly marked `sanitized-rendered-callback-shape`; it is not an exact replay of the old raw request. Dynamic legacy ViewState/ClientWindow values were redacted, and current CSRF/ViewState values were supplied only for authorized test actors.
- The saved workflow result now records authenticated identities as server-verified principal/roles only; it omits CSRF tokens.
- The old browser-generated parameter names and callback values are recorded in `legacy-rendered-callbacks.json` and hash-validated by `tests/security/handling_retirement_evidence.py`.

The callback proof is validated by `run_browser.py` and wired into `current_capabilities.py` retirement observations. The corrected fresh integrated run completed with candidate 777/777 and browser 958/958 checks passing and cleanup complete. The independent promotion review approved ACTION-36, ACTION-37, ACTION-38, ACTION-39 and ACTION-42 for `RETIRED` under the user-approved policy. The source-bound receipt and offline replay in `tests/security/replay_handling_callback_retirement.py` promote exactly 20 actor/action rows while preserving all other 56 retirement rows. Updated totals are 470 current `PASS`, 64 `RETIRED`, and 12 `BLOCKED`; gate exit remains 2 because unrelated retirement blockers remain. `RETIRED` never counts as `PASS`. The replay is offline and does not repeat the live run.

The first run before identity sanitization failed at callback validation and emitted no aggregate report. The corrected fresh run emitted `.work/kan15-handling-callback-retirement/live-results.json` and passed the runner. Per-component reports under the ignored `.work/kan15-handling-callback-retirement/` directory are temporary review artifacts and must not be committed or published.

## Container/image recovery incident

During isolation work, a shared Docker image tag was overwritten before the run-specific image namespace change landed. The running `ai-modernization-kan18` container itself was not replaced: it remains container `69e3b52dec053ee8d406e414c050f65ae2877f2e5399fcb64fb40b5639276644`, using image `sha256:5c8b76eb64ab4e7d06f2d1eb102828623ecc85676ee029a3aaf4dcd848f4d4e2`.

The shared tag `ai-modernization-kan18:candidate` was rebuilt and currently resolves to `sha256:2d1f193039ba2c21aae1ffd3a8bbd6ec74b79f56c5745c9c8d2fa196ec0de372`. This is not the image used by the running KAN-18 container. The rebuilt WAR differs from the WAR extracted from that running container (SHA-256 values: rebuilt `bd8e2bf6dbadaf87c1a8172c002273a544778e730a674db116f3be01ffb3d0d7`; running container `e38671e1286ce0993db95d68102b7cefb55166a0fa54460281d28ac2fe61b693`). Do not recreate KAN-18 from the current shared tag until the owner chooses to accept it or the exact prior image is restored.

The shared browser tag `ai-modernization-kan19:browser` was also rebuilt to `sha256:c9c5d4ac36a9d00f537355fd7637f6083d746e7e20d914c16171ac3f74add4a6`; the prior exact tag digest was not captured, so exact restoration cannot be asserted. The KAN-15 candidate/browser images used for the fresh run were isolated under unique run-specific tags. The owned run containers and network have been cleaned up. The separate KAN-18 running container remains up and unchanged.

Future non-default run IDs now generate unique candidate and browser image tags; the default KAN-18/KAN-19 names remain unchanged for their normal workflow.
