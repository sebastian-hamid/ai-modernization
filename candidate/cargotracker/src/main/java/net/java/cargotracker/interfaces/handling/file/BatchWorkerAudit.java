package net.java.cargotracker.interfaces.handling.file;

import jakarta.annotation.Resource;
import jakarta.annotation.security.RolesAllowed;
import jakarta.ejb.SessionContext;
import jakarta.ejb.Stateless;
import java.util.logging.Logger;

/** Records the actual asynchronous batch caller, separately from the human initiator. */
@Stateless
@RolesAllowed("BatchWorker")
public class BatchWorkerAudit {
    private static final Logger LOGGER = Logger.getLogger(BatchWorkerAudit.class.getName());

    @Resource
    private SessionContext sessionContext;

    public void jobStarted(String runId, String initiator) {
        record("started", runId, initiator);
    }

    public void jobFinished(String runId, String initiator, String status) {
        record("finished:" + status, runId, initiator);
    }

    private void record(String event, String runId, String initiator) {
        String worker = sessionContext.getCallerPrincipal().getName();
        if (!"batch-worker".equals(worker)) {
            throw new SecurityException("Batch execution identity was not the dedicated worker");
        }
        if (runId == null || runId.isBlank() || initiator == null || initiator.isBlank()) {
            throw new SecurityException("Batch run correlation is incomplete");
        }
        LOGGER.info(() -> "IMPORT_AUDIT event=" + event + " runId=" + runId
                + " initiator=" + initiator + " worker=" + worker);
    }
}
