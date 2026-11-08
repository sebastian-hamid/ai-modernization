package net.java.cargotracker.interfaces.handling.file;

import java.util.Date;
import java.util.logging.Level;
import java.util.logging.Logger;
import jakarta.batch.api.listener.JobListener;
import jakarta.batch.runtime.BatchRuntime;
import java.util.Properties;
import jakarta.enterprise.context.Dependent;
import jakarta.batch.runtime.context.JobContext;
import jakarta.inject.Inject;
import jakarta.inject.Named;

@Dependent
@Named("FileProcessorJobListener")
public class FileProcessorJobListener implements JobListener {

    private static final Logger logger = Logger.getLogger(
            FileProcessorJobListener.class.getName());
    @Inject
    private JobContext jobContext;
    @Inject
    private BatchWorkerAudit workerAudit;

    @Override
    public void beforeJob() throws Exception {
        Properties parameters = BatchRuntime.getJobOperator().getParameters(jobContext.getExecutionId());
        workerAudit.jobStarted(parameters.getProperty("import_run_id"),
                parameters.getProperty("import_initiated_by"));
        logger.log(Level.INFO,
                "Handling event file processor batch job starting at {0}",
                new Date());
    }

    @Override
    public void afterJob() throws Exception {
        logger.info(() -> "BATCH_AFTER_JOB_BEGIN executionId=" + jobContext.getExecutionId()
                + " status=" + jobContext.getBatchStatus());
        Properties parameters = BatchRuntime.getJobOperator().getParameters(jobContext.getExecutionId());
        workerAudit.jobFinished(parameters.getProperty("import_run_id"),
                parameters.getProperty("import_initiated_by"),
                String.valueOf(jobContext.getBatchStatus()));
        logger.info(() -> "BATCH_AFTER_JOB_AUDIT_RETURN executionId=" + jobContext.getExecutionId());
        logger.log(Level.INFO,
                "Handling event file processor batch job completed at {0}",
                new Date());
    }
}
