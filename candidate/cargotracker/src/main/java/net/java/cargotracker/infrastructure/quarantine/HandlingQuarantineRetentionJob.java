package net.java.cargotracker.infrastructure.quarantine;

import jakarta.ejb.EJB;
import jakarta.ejb.Schedule;
import jakarta.ejb.Singleton;
import jakarta.ejb.Startup;
import java.util.logging.Level;
import java.util.logging.Logger;

/** Removes quarantine rows after their configured retention and releases capacity. */
@Singleton
@Startup
@jakarta.annotation.security.RunAs("HandlingQuarantineWorker")
public class HandlingQuarantineRetentionJob {
    private static final Logger LOG = Logger.getLogger(HandlingQuarantineRetentionJob.class.getName());
    @EJB
    private HandlingAttemptQuarantineService quarantineService;

    @Schedule(hour = "*", minute = "*", second = "*", persistent = false)
    public void purgeExpired() {
        try {
            int removed = quarantineService.purgeExpired();
            if (removed > 0) LOG.info("HANDLING_QUARANTINE_RETENTION_PURGED count=" + removed);
        } catch (RuntimeException failure) {
            LOG.log(Level.WARNING, "Handling quarantine retention cleanup failed; no entries were acknowledged by this job.");
        }
    }
}
