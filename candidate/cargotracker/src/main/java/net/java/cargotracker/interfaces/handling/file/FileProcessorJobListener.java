package net.java.cargotracker.interfaces.handling.file;

import java.util.Date;
import java.util.logging.Level;
import java.util.logging.Logger;
import jakarta.batch.api.listener.JobListener;
import jakarta.enterprise.context.Dependent;
import jakarta.inject.Named;

@Dependent
@Named("FileProcessorJobListener")
public class FileProcessorJobListener implements JobListener {

    private static final Logger logger = Logger.getLogger(
            FileProcessorJobListener.class.getName());

    @Override
    public void beforeJob() throws Exception {
        logger.log(Level.INFO,
                "Handling event file processor batch job starting at {0}",
                new Date());
    }

    @Override
    public void afterJob() throws Exception {
        logger.log(Level.INFO,
                "Handling event file processor batch job completed at {0}",
                new Date());
    }
}
