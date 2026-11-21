# KAN-25 expiry and backlog observation

A disposable candidate runtime was built from the current working tree. The probe submitted two validly formatted LOAD reports for deliberately unknown tracking IDs (NOCARGO1 and NOCARGO2) through the authenticated handling endpoint. Each POST returned HTTP 204; asynchronous processing was measured through WildFly queue counters, application invocation counters, and before/after database table digests.

## Expiry while queued

The handling-attempt queue was paused before submitting the first report. After the configured 30,000 ms TTL had elapsed, the paused queue still showed one message, no expiration increment, and no handler invocation. On resume, the attempt queue drained, MessagesExpired increased by one, and one message appeared in ExpiryQueue. The handling and rejection consumers were not invoked, and database tables remained unchanged. This is evidence of broker expiry disposition for this single aged message; it does not establish how long the expiry queue retains or processes it.

## Backlog recovery

The queue was paused again, a second report entered it, and the queue resumed after approximately one second, well before the TTL. The backlog drained through three handler invocations (the original delivery plus two redeliveries), one transfer to RejectedRegistrationAttemptsQueue, and one acknowledgment by the rejection consumer. Both observed queue counts returned to zero, and database table digests were unchanged.

## Run and limits

The final disposable run passed 20 bootstrap assertions and all 58 candidate domain tests (zero failures, errors, or skips). Its app container and private credential files were removed with no cleanup errors. The probe source was temporary and no application code, runtime configuration, or permanent test was changed for this observation. Earlier harness attempts exposed two harness issues (a non-runtime queue address and an observer snapshot error); the final run used WildFly's runtime-queue address and completed both observations. The failed attempts also cleaned up their containers and credentials.

This evidence does not establish high-volume behavior, broker restart durability, or downstream retention/replay for expired messages. It does not resolve whether expired or exhausted payloads should be retained for operator review, whether a stable submission ID should suppress transport-level duplicate posts, or what loss policy the product accepts. Those policy choices remain pending. Existing duplicate replay evidence shows repeated submissions create repeated work; this observation does not claim exactly-once processing.

See [summary.json](summary.json) for the measured counters, run identifier, image digest, and cleanup receipt.
