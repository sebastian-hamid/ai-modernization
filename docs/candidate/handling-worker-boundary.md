# Handling message worker boundary

The handling form and REST adapter accept reports from authorized Operator and Administrator sessions. Those human roles initiate supported actions through the application layer; they do not receive the internal HandlingWorker role.

Direct calls to the handling-registration service are restricted by its EJB role check. The HandlingEventRegistrationAttemptConsumer MDB runs with the HandlingWorker role and an explicit WildFly run-as principal, handling-worker. Before delegating an event, it calls HandlingWorkerAudit, which checks the server principal and role and records a sanitized audit marker. If either check fails, the message transaction does not reach the business service.

The disposable fixture directly calls the EJB with anonymous, Reader, Operator, and Administrator request identities and observes database, JMS, and invocation state around each denial. It separately observes actual queue processing after authorized Operator and Administrator submissions and binds each MDB invocation to a successful handling-worker audit record.

The audit verifies the in-process EJB/MDB identity boundary. It does not by itself prove remote broker credentials, external JMS/JNDI network access restrictions, crash replay deduplication, or producer identity propagation. Those machine and recovery checks remain separate acceptance work.

## Fresh remote broker producer boundary

A separate-JVM remote+http JMS probe now verifies the broker side of the BG-03 boundary. It forces broker authentication before each send attempt. The trusted handling-attempt-producer can send to HandlingEventRegistrationAttemptQueue. Anonymous, Reader, Operator, Administrator, BatchWorker, HandlingWorker, InspectionWorker, and NotificationWorker cannot send to that queue. The trusted producer also cannot send to RejectedRegistrationAttemptsQueue or DeliveredCargoQueue. Only explicit JMS security denial from the send call counts; setup, authentication, connection, and unrelated failures fail the fixture. Unauthorized table effects remained unchanged.

The fresh current-capability gate binds the raw principal and send-denial results to the same-fixture worker identity and authorized adapter events. CURRENT::BG-03-MACHINE::worker-BG-03::active passes. See the sanitized run in notes/evidence/kan-15-bg03-producer-boundary/validation.json and its current-capability-gate.json.

This verifies the disposable candidate WildFly configuration and the named principals exercised by the fixture. It is not a production deployment or a claim that every external principal, JNDI binding, host policy, or broker configuration has been audited. BG-04 protects a different queue and remains separately blocked until its producer boundary is tested.
