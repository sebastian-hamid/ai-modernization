package net.java.cargotracker.interfaces.handling.file;

import java.io.File;
import java.io.PrintWriter;
import java.util.logging.Level;
import java.util.logging.Logger;
import jakarta.batch.api.chunk.listener.SkipReadListener;
import jakarta.batch.runtime.context.JobContext;
import jakarta.enterprise.context.Dependent;
import jakarta.inject.Inject;
import jakarta.inject.Named;

@Dependent
@Named("LineParseExceptionListener")
public class LineParseExceptionListener implements SkipReadListener {

    private static final String FAILED_DIRECTORY = "failed_directory";
    private static final Logger logger = Logger.getLogger(
            LineParseExceptionListener.class.getName());
    @Inject
    private JobContext jobContext;

    @Override
    public void onSkipReadItem(Exception e) throws Exception {
        EventLineParseException parseException = (EventLineParseException) e;

        logger.log(Level.WARNING, "Problem parsing event file line",
                parseException);

        String filename = "failed_" + jobContext.getJobName()
                + "_" + jobContext.getInstanceId() + ".csv";
        try (PrintWriter failed = new PrintWriter(BatchImportPaths.openAppendOutput(
                BatchImportPaths.FAILED,
                jobContext.getProperties().getProperty(FAILED_DIRECTORY), filename))) {
            failed.println(parseException.getLine());
        }
    }
}
