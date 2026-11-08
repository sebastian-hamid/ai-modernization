# KAN-15 BG-02 trusted batch file processing

## Scope

This increment binds the four BG-02 human actor cases to the migrated batch processing boundary: CURRENT::BG-02::{anonymous,Reader,Operator,Administrator}::active. It verifies that only an Administrator can initiate the controlled import and that the actual JBeret worker uses its dedicated server identity.

The separate BG-02-MACHINE::worker-BG-02::active case remains BLOCKED. The run proves the batch worker identity, but does not independently attest a trusted filesystem producer identity or a producer-to-worker machine scope.

## Verified behavior

- The disposable runtime sets incoming, archive, and failed to mode 700 and verifies that their owner UID is the WildFly process UID.
- An Administrator starts the fixed import job through the CSRF- and ViewState-protected form. The job audit identifies the actual worker as batch-worker.
- The valid staged RECEIVE event is consumed, written to a generated archive file within the approved archive directory, and persisted with the expected database and JMS effects.
- A malformed staged line is consumed and recorded exactly once under the generated failed-file name. It is absent from the archive, and it causes no additional business effects.
- Anonymous, Reader, and Operator import attempts remain denied; direct JobOperator read/start probes and settled independent effects remain covered.
- No HTTP file-upload or arbitrary job-selection endpoint is added.

## Fresh validation

The full browser-backed gate completed with a matching pre-run and post-run input fingerprint (40a41feba5019ca3d404d99f8518597057f3f46ae8aa49f3a6fe42c5f11ae439).

- Native runtime: 699 checks passed.
- Chromium browser workflow: 841 checks passed.
- Current capability gate: 432 PASS / 38 BLOCKED.
- BG-02 human cases: all four PASS.
- BG-02 machine case: BLOCKED pending dedicated machine-scope evidence.
- Retirement inventory: 76 BLOCKED; historical audit remains 324 PASS / 178 BLOCKED.
- Focused regression suites: 85 security, 42 candidate-runtime, and 30 browser-workflow tests passed.
- Fixture cleanup: private credentials removed, owned app/browser resources removed, and no cleanup errors.

The expected gate exit code is 2 while blocked cases remain. The full result is [validation.json](validation.json). Its provenance notes that on-disk input fingerprints are bound but imported Python code identity is not attested.

## Attempt history

Running tests/candidate-runtime/run_candidate.py --help unexpectedly launched the native fixture because that lower-level runner has no argument parser. That native run passed 699 checks and cleaned its credentials and container. An immediately following full gate launch then stopped at the existing private-file guard while that native run still owned its fixture, preventing a duplicate. After native cleanup, the full wrapper was launched once and completed with the browser and gate results above.

## Independent review

An independent read-only review approved the four BG-02 human cases with no material finding. The reviewer replayed all three result arrays and confirmed that exactly four intended cases changed. The filesystem/archive assertions are recorded by the disposable fixture; trusted producer identity, crash recovery, and machine-scope acceptance remain outside this promotion.
