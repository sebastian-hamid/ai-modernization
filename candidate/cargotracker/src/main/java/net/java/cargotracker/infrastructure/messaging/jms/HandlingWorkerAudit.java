package net.java.cargotracker.infrastructure.messaging.jms;

import jakarta.annotation.Resource;
import jakarta.annotation.security.RolesAllowed;
import jakarta.ejb.SessionContext;
import jakarta.ejb.Stateless;
import java.util.logging.Logger;

/** Verifies and records the dedicated identity used by the handling-event consumer. */
@Stateless
@RolesAllowed("HandlingWorker")
public class HandlingWorkerAudit {
    private static final Logger LOGGER = Logger.getLogger(HandlingWorkerAudit.class.getName());

    @Resource
    private SessionContext sessionContext;

    public void recordConsumedAttempt() {
        String principal = sessionContext.getCallerPrincipal().getName();
        boolean workerRole = sessionContext.isCallerInRole("HandlingWorker");
        if (!"handling-worker".equals(principal) || !workerRole) {
            throw new SecurityException("Handling event consumer did not run as its dedicated worker");
        }
        LOGGER.info("HANDLING_WORKER_AUDIT event=consumed principal=handling-worker role=HandlingWorker");
    }
}
