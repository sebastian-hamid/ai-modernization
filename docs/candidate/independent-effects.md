# Disposable candidate effects observers (KAN-15)

## Purpose and verified scope

HTTP rejection and unchanged REST output alone cannot demonstrate absence of side effects. The disposable candidate fixture now observes the database directly, actual broker counters and business/worker invocations independently of the application's monitor endpoint.

The runtime checks use the same well-formed handling payload as an allowed control for anonymous401, Reader403 and missing/wrong-CSRF403 requests. They additionally replay an Operator-rendered booking callback as Reader with a real Reader CSRF token, and as Operator without CSRF. The forged cross-role ViewState is an authorization replay fixture; this does not claim that Faces would accept that view as Reader after bypassing authorization.

Separate mutation-capable Operator sessions are authenticated with server-verified role, logged out or left without HTTP traffic for75 seconds in the one-minute-session lab, then their saved cookies and CSRF tokens replay the handling POST. Identity endpoints also confirm revocation. Each denied cohort has equal independent before/after snapshots. This is bounded observed absence for these requests, not completion of all502 desired-access definitions.

An allowed Operator report must change SQL content hashes and cumulative queue counters, and increment registerHandlingEvent plus both HandlingEventRegistrationAttemptConsumer#onMessage and CargoHandledConsumer#onMessage. This positive control proves the observers are connected to actual application processing; empty/disconnected observations cannot substitute for success.

## Architecture and isolation

Only tests/candidate-runtime/Dockerfile overlays observer Java classes and a default EJB interceptor descriptor into its copied disposable WAR. Candidate application sources, default persistence.xml and normal Maven WAR do not contain this instrumentation. The existing disposable opt-in and JVM flag are required. The filesystem import scanner remains disabled.

LabEffects registers a local platform MBean. A separate Java helper, executed as the container user, attaches to the unique WildFly JVM and starts its local management connector. No HTTP observer endpoint, remote JMX listener, new host port or observer credential is introduced. Docker/host control remains a test-control-plane privilege; human application roles are not granted it.

- SQL observer obtains ExampleDS independently of repositories/monitor DTOs. It reads all PUBLIC application tables, sorts complete JSON-encoded row values (including IDs) and records counts plus SHA256 hashes. It executes fixed SELECT statements using quoted metadata names, no caller SQL.
- Broker JMX is enabled only in the disposable container configuration. All registered queues are captured, with required application queues, DLQ and ExpiryQueue; missing required observers fail. Snapshots include MessageCount, DeliveringCount, ScheduledCount, MessagesAdded, MessagesAcknowledged, MessagesExpired, MessagesKilled and AcknowledgeAttempts. Cumulative counters detect enqueue-then-consume that depth alone misses.
- A lab-only @AroundInvoke interceptor counts method entries on EJB business methods and MDB onMessage. Repeated worker invocation is visible even if queue depth returns to zero. No arguments, identities, cookies or credentials are recorded. This is test invocation telemetry, not a production business/security audit implementation. Timer @AroundTimeout callbacks are not instrumented.
- Each snapshot flushes broker queue executors. Settlement requires three equal snapshots with no queued/delivering/scheduled messages, separated by0.5-second waits, with a15-second loop budget. Each command separately times out after30 seconds; the loop budget is not a strict wall-clock upper bound. Missing/failed/unstable observers fail the runtime check. No counter is reset.

An initially empty business-call history may be legitimate, but the current fixture has real read calls and the allowed control must demonstrate specific mutation/worker increments. Hashes/counters are fixture-scoped; comparing across restarts is invalid.

## Reproduction and limits

From WSL repository root:

    python3 tests/browser-workflows/run_browser.py
    python3 -m unittest discover -s tests/candidate-runtime -p 'test_*.py' -v
    python3 -m unittest discover -s tests/browser-workflows -p test_browser_harness.py -v

Sanitized final runtime/browser results and exact inputs are stored under notes/evidence/kan-15-effects. Credentials, cookies, full rows and raw logs are not published. The fixture removes its owned app/browser/network and private realm/client files; shared historical app and Jenkins are preserved.

The observation window cannot rule out every arbitrarily delayed effect. Successful handling is observed through the actual two-worker chain, but full poison-message/retry/restart disposition, direct machine/broker/filesystem controls, every callback/method, and full502 adapter execution remain separate. The top-level denied_write_absence_verified flag remains false so these scoped successes cannot silently turn the entire security gate green. H2 lab evidence does not prove PostgreSQL behavior, production auditability, or deployed security.

## Live catalogue adapter

Run python3 tests/security/run_candidate_contracts.py --live-subset to launch a fresh disposable runtime and pass its explicit observations into the existing fail-closed oracle. Only API-02 anonymous/Reader active denials and Operator logged_out/expired handling replays are currently bound. All other catalogue cases remain BLOCKED and the full gate exits2. The default command stays non-live/all-BLOCKED; it never consumes archived reports as fresh execution.

Each bound denial includes inspected response absence of fixture cargo markers, real HTTP status, server-verified role where applicable, and fixture-matched independent snapshots. Active anonymous/Reader cases share the explicitly recorded denial cohort window; its cumulative counters and invocation history must remain equal. These four bindings do not cover allowed handling semantics in the catalogue, although the runtime's positive control verifies processing independently. They do not establish every HTTP error body is free of every possible secret.

Broker counter meanings follow the official [Artemis QueueControl API](https://artemis.apache.org/components/artemis/documentation/javadocs/javadoc-latest/org/apache/activemq/artemis/api/core/management/QueueControl.html). The pinned runtime's actual exposed attributes and worker connectedness are checked by the live fixture.

The oracle also recognizes403/404 for direct internal-template requests, consistent with their deny-every-identity inventory classification. This exception never treats an operational page404 as successful authorization, and does not add any template case to the live subset.
