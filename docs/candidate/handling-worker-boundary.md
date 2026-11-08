# Handling message worker boundary

The handling form and REST adapter accept reports from authorized Operator and Administrator sessions. Those human roles initiate supported actions through the application layer; they do not receive the internal HandlingWorker role.

Direct calls to the handling-registration service are restricted by its EJB role check. The HandlingEventRegistrationAttemptConsumer MDB runs with the HandlingWorker role and an explicit WildFly run-as principal, handling-worker. Before delegating an event, it calls HandlingWorkerAudit, which checks the server principal and role and records a sanitized audit marker. If either check fails, the message transaction does not reach the business service.

The disposable fixture directly calls the EJB with anonymous, Reader, Operator, and Administrator request identities and observes database, JMS, and invocation state around each denial. It separately observes actual queue processing after authorized Operator and Administrator submissions and binds each MDB invocation to a successful handling-worker audit record.

The audit verifies the in-process EJB/MDB identity boundary. It does not by itself prove remote broker credentials, external JMS/JNDI network access restrictions, crash replay deduplication, or producer identity propagation. Those machine and recovery checks remain separate acceptance work.
