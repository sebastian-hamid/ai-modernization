# KAN-15 BG-01 batch import evidence

The disposable candidate runtime passed 696 checks. Its 35 candidate domain tests passed with 0 failures, errors, or skips. [results.json](results.json) contains the sanitized run output, and [validation.json](validation.json) summarizes the verified gates and artifact hashes.

Verified denial paths include anonymous import GET and POST, direct JobOperator read/start/restart under Reader, Operator, and Administrator identities, disabled-switch backend rejection, missing and wrong CSRF, revoked Administrator session, concurrent reuse of a one-time form, sequential replay, symlink and non-regular staged entries. The off-switch test issued a nonce while enabled, switched the backend off, then called the request service directly and observed request-service start +1 with launcher start +0; the staged marker remained and no job submission occurred.

The authorized empty import ran as batch-worker and left business state unchanged. A valid RECEIVE event persisted to independent Reader state and produced the expected settled JMS queue cycles and bounded invocation deltas. The report records expected and observed control EJB deltas; they match exactly: issueNonce +3, request-service start +4, launcher start +3, worker start/finish +1 each, with all other invocation counters unchanged in that interval.

The BatchApiProbe servlet is injected only into the disposable build context by the test harness. It is absent from candidate source and production WAR configuration. The owned container and generated credentials were removed; cleanup errors were empty. No shared baseline or Jenkins container was used, and synced sources/ were not modified.

This evidence covers BG-01 initiation only. It does not complete KAN-15's overall access acceptance inventory or later batch recovery, crash deduplication, and independent worker/broker boundary work (BG-02 through BG-05). Independent review approved the BG-01 scope; KAN-15 remains In Progress.
