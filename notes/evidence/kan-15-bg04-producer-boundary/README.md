# KAN-15 BG-04 CargoHandledQueue producer boundary

Date: 9 November 2026

## Scope

The disposable WildFly fixture exercises CargoHandledQueue authorization through a separate JVM using the remote+http JMS endpoint. It verifies authentication before each send and accepts only broker-specific send authorization failures as denials.

The named HandlingWorker account is authenticated and allowed to submit a canonical metadata-bearing message in a transacted JMS session. The probe rolls the transaction back after the send call. Anonymous, Reader, Operator, Administrator, BatchWorker, InspectionWorker, and NotificationWorker are denied send access. The fixture confirms that application tables, CargoHandledQueue counters, CargoHandledConsumer invocation count, and InspectionWorkerAudit count are unchanged around this probe. Normal application handling events remain separately verified through the handling adapter and consumer, with server-generated correlations and InspectionWorker identity audits.

## Result

The BG-04 machine case passes in the fresh current-capability gate. The native fixture passed 724 checks; Chromium passed 841 checks. All owned containers, the browser network, and private credential files were removed. The gate reports 448 PASS / 22 BLOCKED current cases, 324 PASS / 178 BLOCKED historical cases, and 76 BLOCKED retirement cases. Gate exit 2 is expected while cases remain blocked.

The input fingerprint is `a656082f4193d00de715d2a048a72167aceff02a4838802b370d7feebd5360d3`. See [validation summary](validation.json) and the [full sanitized current gate](current-capability-gate.json).

## Limits

This verifies only the disposable candidate configuration and named fixture principals. It does not audit production WildFly settings, arbitrary external JNDI clients, host/network policy, unlisted broker identities, or credential distribution. Anyone holding the HandlingWorker credential has the broker permission tested here. The `producerOrigin` property and correlation UUID are message metadata, not cryptographic proof of which application component created the message.
