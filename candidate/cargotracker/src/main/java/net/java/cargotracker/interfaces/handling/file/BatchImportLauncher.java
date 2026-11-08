package net.java.cargotracker.interfaces.handling.file;

import jakarta.annotation.Resource;
import jakarta.annotation.security.RolesAllowed;
import jakarta.annotation.security.RunAs;
import jakarta.batch.operations.JobOperator;
import jakarta.batch.runtime.BatchRuntime;
import jakarta.ejb.Stateless;
import jakarta.ejb.SessionContext;
import java.util.Properties;
import java.util.List;
import java.util.logging.Logger;

/** Narrow EJB boundary that starts only the fixed import job under its worker identity. */
@Stateless
@RolesAllowed("BatchTrigger")
@RunAs("BatchWorker")
public class BatchImportLauncher {
    private static final Logger LOGGER = Logger.getLogger(BatchImportLauncher.class.getName());

    @Resource
    private SessionContext sessionContext;

    public long start(String runId, String initiator) {
        if (!"batch-trigger".equals(sessionContext.getCallerPrincipal().getName())) {
            throw new SecurityException("Expected the dedicated batch trigger identity");
        }
        try {
            if (BatchImportPaths.incomingFiles(BatchImportPaths.INCOMING.toString()).isEmpty()) {
                throw new IllegalStateException("No staged import files are available");
            }
        } catch (java.io.IOException failure) {
            throw new IllegalStateException("Import staging directory is unavailable or unsafe", failure);
        }
        JobOperator operator = BatchRuntime.getJobOperator();
        List<Long> running = operator.getRunningExecutions(BatchImportPaths.JOB_NAME);
        if (!running.isEmpty()) {
            throw new IllegalStateException("An import job is already running");
        }
        Properties parameters = new Properties();
        parameters.setProperty("import_run_id", runId);
        parameters.setProperty("import_initiated_by", initiator);
        LOGGER.info(() -> "IMPORT_JOB_SUBMIT runId=" + runId
                + " initiator=" + initiator + " trigger=batch-trigger worker=batch-worker");
        long executionId = operator.start(BatchImportPaths.JOB_NAME, parameters);
        LOGGER.info(() -> "IMPORT_JOB_STARTED runId=" + runId + " executionId=" + executionId);
        return executionId;
    }
}
