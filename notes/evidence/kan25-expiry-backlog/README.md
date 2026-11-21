# KAN-25 expiry and backlog observation

A disposable candidate runtime was built from the current working tree. The probe submitted two validly formatted LOAD reports for deliberately unknown tracking IDs (NOCARGO1 and NOCARGO2) through the authenticated handling endpoint. Each POST returned HTTP 204; asynchronous processing was measured through WildFly queue counters, application invocation counters, and before/after database table digests.

## Expiry while queued

The handling-attempt queue was paused before submitting the first report. After the configured 30,000 ms TTL had elapsed, the paused queue still showed one message, no expiration increment, and no handler invocation. On resume, the attempt queue drained, MessagesExpired increased by one, and one message appeared in ExpiryQueue. The handling and rejection consumers were not invoked, and database tables remained unchanged. This is evidence of broker expiry disposition for this single aged message; it does not establish how long the expiry queue retains or processes it.

## Backlog recovery

The queue was paused again, a second report entered it, and the queue resumed after approximately one second, well before the TTL. The backlog drained through three handler invocations (the original delivery plus two redeliveries), one transfer to RejectedRegistrationAttemptsQueue, and one acknowledgment by the rejection consumer. Both observed queue counts returned to zero, and database table digests were unchanged.

## Run and limits

The final disposable run passed 20 bootstrap assertions and all 58 candidate domain tests (zero failures, errors, or skips). Its app container and private credential files were removed with no cleanup errors. The probe source was temporary and no application code, runtime configuration, or permanent test was changed for this observation. Earlier harness attempts exposed two harness issues (a non-runtime queue address and an observer snapshot error); the final run used WildFly's runtime-queue address and completed both observations. The failed attempts also cleaned up their containers and credentials.

This evidence does not establish high-volume behavior, broker restart durability, or downstream retention/replay for expired messages. The user subsequently approved bounded quarantine with restricted operator review and controlled manual replay, but runtime implementation and enforcement of the approved retention and capacity bounds are unverified. Whether a stable submission ID should suppress transport-level duplicate posts and what loss policy applies after quarantine disposal remain pending. Existing duplicate replay evidence shows repeated submissions create repeated work; this observation does not claim exactly-once processing.

See [summary.json](summary.json) for the measured counters, run identifier, image digest, and cleanup receipt.

## TTL decision and remaining policy

On 21 November 2026, the user approved keeping the candidate handling-attempt TTL at 30 seconds. The earlier 1-second value in Jira was stale; Jira was corrected to match the configured value. No runtime configuration or application behavior changed for this decision.

At the time of the probe, policy choices were pending. The subsequent bounded-quarantine decision and remaining operational questions are recorded below. The single-message probe does not establish downstream expiry-queue retention or processing.


## Bounded quarantine decision

On 21 November 2026, the user approved bounded quarantine for expired or exhausted messages. The intended disposition is restricted operator review and explicitly controlled manual replay; automatic replay is not approved. The single-message observation proves that one expired message entered the broker ExpiryQueue, but does not verify downstream retention, access controls, replay tooling, capacity behavior, or eventual disposal. This is a policy decision only: no runtime configuration or application behavior changed. On 21 November 2026, the user approved a maximum retention window of 7 days before disposal. The 7-day policy duration is set, but runtime retention and disposal behavior remain unimplemented and unverified. The user approved a 1 GiB quarantine capacity limit; behavior at capacity remains to be decided and verified. Submission idempotency and acceptable-loss policy also remain open.
