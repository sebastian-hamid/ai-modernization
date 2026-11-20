# Handling report input validation — KAN-24

The protected POST /rest/handling/reports endpoint accepts syntactically valid report data and publishes one asynchronous registration attempt. Malformed request data returns HTTP 400 before publication. The response uses a generic Invalid handling report message rather than exposing parsing or domain-constructor details. Existing role and CSRF protections are unchanged.

## Functional contract

- eventType must exactly match a HandlingEvent.Type enum name.
- unLocode must pass the domain value object's syntax validation. A well-formed but unknown location remains a later lookup/business-processing outcome; this change does not resolve locations synchronously.
- completionTime uses the full yyyy-MM-dd HH:mm shape, with strict calendar validity. Impossible dates and trailing or partial text are rejected. A valid local date/time is converted using the process default time zone, preserving the endpoint's prior local-time interpretation.
- Invalid report fields, event types, location codes, dates, tracking IDs, or voyage numbers return HTTP 400. No registration-attempt queue message or database write is produced by malformed requests.
- Valid reports continue through the existing asynchronous handling workflow. A successful HTTP response alone is not a guarantee of later business acceptance.

## Architecture and implementation

HandlingReportService parses and constructs all request values before calling ApplicationEvents.receivedHandlingEventRegistrationAttempt. DateTimeFormatter uses ResolverStyle.STRICT; LocalDateTime.parse requires complete input consumption. BadRequestException translates expected conversion errors to HTTP 400. The asynchronous event, worker, transaction and persistence design is otherwise unchanged.

## Verification

A fresh disposable Java 25/WildFly candidate runtime passed 795 checks, including 58 candidate domain/characterization tests (0 failures/errors/skips). Four authenticated malformed POST cases (invalid enum, malformed UN/LOCODE, impossible date, and 16-character partial/trailing date content) each returned sanitized HTTP 400. Before/after SQL content hashes and row counts matched; all broker queue counters matched; the only business invocation delta was exactly four calls to HandlingReportService.submitReport, with no downstream business invocation. Existing positive handling paths in the same suite passed. Fixture cleanup removed its container and private credentials without errors. KAN-18 and Jenkins remained unchanged. Machine-readable result: [summary](../../notes/evidence/kan24-malformed-handling-inputs/summary.json). Source hashes: [input-sha256.json](../../notes/evidence/kan24-malformed-handling-inputs/input-sha256.json).

The final live KAN-24 run also verified the approved CLAIM/later-LOAD rule: a cargo was claimed, then a validly shaped LOAD was posted. The worker rejected the LOAD based on persisted handling history; the handling-event table and cargo state stayed unchanged. The attempt followed three bounded worker deliveries and the existing rejected-registration queue path. See [load-after-claim evidence](../../notes/evidence/kan24-load-after-claim/summary.json). Independent service tests verify that a LOAD is rejected before event creation/storage/publication and that non-LOAD types are not blocked by this rule.

This is a candidate fixture result, not production deployment evidence. It does not establish external broker behavior, forced transaction rollback, or concurrent CLAIM/LOAD race behavior. The historical source behavior remains preserved in the legacy characterization notes.
