package net.java.cargotracker.interfaces.handling.file;

import java.io.File;
import java.io.PrintWriter;
import java.io.Serializable;
import java.util.List;
import java.util.Properties;
import java.util.logging.Logger;
import jakarta.batch.runtime.BatchRuntime;
import jakarta.batch.api.chunk.AbstractItemWriter;
import jakarta.batch.runtime.context.JobContext;
import jakarta.enterprise.context.Dependent;
import jakarta.inject.Inject;
import jakarta.inject.Named;
import jakarta.transaction.Transactional;
import net.java.cargotracker.application.ApplicationEvents;
import net.java.cargotracker.interfaces.handling.HandlingEventRegistrationAttempt;

@Dependent
@Named("EventItemWriter")
public class EventItemWriter extends AbstractItemWriter {

    private static final Logger LOGGER = Logger.getLogger(EventItemWriter.class.getName());
    private static final String ARCHIVE_DIRECTORY = "archive_directory";
    @Inject
    private JobContext jobContext;
    @Inject
    private ApplicationEvents applicationEvents;

    @Override
    public void open(Serializable checkpoint) throws Exception {
        BatchImportPaths.requireDirectory(BatchImportPaths.ARCHIVE,
                jobContext.getProperties().getProperty(ARCHIVE_DIRECTORY));
    }

    @Override
    @Transactional
    public void writeItems(List<Object> items) throws Exception {
        long executionId = jobContext.getExecutionId();
        Properties parameters = BatchRuntime.getJobOperator().getParameters(executionId);
        String runId = parameters.getProperty("import_run_id");
        LOGGER.info(() -> "BATCH_WRITE_BEGIN runId=" + runId + " executionId="
                + executionId + " itemCount=" + items.size());
        String filename = "archive_" + jobContext.getJobName()
                + "_" + jobContext.getInstanceId() + ".csv";
        try (PrintWriter archive = new PrintWriter(BatchImportPaths.openAppendOutput(
                BatchImportPaths.ARCHIVE,
                jobContext.getProperties().getProperty(ARCHIVE_DIRECTORY), filename))) {
            for (Object item : items) {
                HandlingEventRegistrationAttempt attempt = (HandlingEventRegistrationAttempt) item;
                LOGGER.info(() -> "BATCH_WRITE_SEND_BEGIN runId=" + runId
                        + " executionId=" + executionId);
                applicationEvents.receivedHandlingEventRegistrationAttempt(attempt);
                LOGGER.info(() -> "BATCH_WRITE_SEND_RETURN runId=" + runId
                        + " executionId=" + executionId);
                archive.println(attempt.getRegistrationTime()
                        + "," + attempt.getCompletionTime()
                        + "," + attempt.getTrackingId()
                        + "," + attempt.getVoyageNumber()
                        + "," + attempt.getUnLocode()
                        + "," + attempt.getType());
                if (archive.checkError()) {
                    throw new java.io.IOException("Archive writer reported an output error");
                }
                LOGGER.info(() -> "BATCH_WRITE_ARCHIVE_ROW runId=" + runId
                        + " executionId=" + executionId);
            }
        }
        LOGGER.info(() -> "BATCH_WRITE_RETURN runId=" + runId + " executionId=" + executionId);
    }
}
