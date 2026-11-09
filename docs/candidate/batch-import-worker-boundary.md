# Batch import worker boundary

## Identity and execution

An authenticated Administrator can stage import files and start the fixed EventFilesProcessorJob through the current application. The request service and launch EJB enforce separate BatchTrigger and BatchWorker run-as boundaries. BatchImportLauncher accepts only the trigger role, verifies the trigger principal, and starts only the fixed job. WildFly maps the worker run-as identity to the batch-worker principal.

FileProcessorJobListener calls BatchWorkerAudit at job start and finish. The audit EJB requires the BatchWorker role and checks the actual SessionContext caller principal is batch-worker before recording the run ID, initiator, and worker. The fixture correlates the valid-file job's start and completed audit entries by run ID and verifies worker=batch-worker; that exact valid-job result backs BG-01-MACHINE. This keeps the Administrator who initiated the job distinct from the machine identity that executes it. The handling-attempt JMS producer has its own dedicated producer identity and remains a separate boundary.

## File boundary and behavior

The candidate uses private server-owned incoming, archive, and failed directories. The reader rejects symbolic links, non-regular files, paths outside the approved directory, and unsafe checkpoints. Valid rows are processed as handling events and archived under generated names. Invalid rows are isolated in failed output without business processing.

## Evidence and limits

The 9 November disposable fixture observed the authorized valid-file job start and complete under batch-worker, persisted exactly one handling event, verified the archive and private directory ownership, and isolated a malformed row in failed output. The independent current-capability replay records BG-01-MACHINE as PASS while preserving the original raw gate report and fingerprint: [sanitized replay evidence](../../notes/evidence/kan-15-bg05-producer-boundary/replacement-gate-replay.json).

This is an Administrator-triggered asynchronous batch job. The evidence verifies the server-side batch execution identity and does not claim that an OS scheduler or production deployment has been configured.


The 9 November BG-02 fixture additionally verifies the OS filesystem boundary: approved fixture administration tooling stages files, the three mode-700 directories are owned by the WildFly process UID, and an unrelated OS UID cannot list/read/write or leave marker files. The valid and malformed inputs follow their intended archive/failure paths. This is disposable-fixture evidence, not a production host ACL attestation. See [BG-02 validation](../../notes/evidence/kan-15-bg02-filesystem-boundary/README.md).
