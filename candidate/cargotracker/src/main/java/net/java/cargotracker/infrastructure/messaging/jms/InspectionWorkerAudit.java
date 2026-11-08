package net.java.cargotracker.infrastructure.messaging.jms;

import jakarta.annotation.Resource;
import jakarta.annotation.security.RolesAllowed;
import jakarta.ejb.SessionContext;
import jakarta.ejb.Stateless;
import java.util.UUID;
import java.util.logging.Logger;

/** Verifies the inspection worker identity and auditable producer metadata. */
@Stateless
@RolesAllowed("InspectionWorker")
public class InspectionWorkerAudit {
    private static final Logger LOGGER = Logger.getLogger(InspectionWorkerAudit.class.getName());

    @Resource
    private SessionContext sessionContext;

    public void recordConsumedAttempt(String correlationId, String producerOrigin) {
        String principal = sessionContext.getCallerPrincipal().getName();
        boolean workerRole = sessionContext.isCallerInRole("InspectionWorker");
        if (!"inspection-worker".equals(principal) || !workerRole) {
            throw new SecurityException("Cargo inspection consumer lacks its dedicated worker identity");
        }
        if (!"handling-event-service".equals(producerOrigin) || !isCanonicalUuid(correlationId)) {
            throw new SecurityException("Cargo handled message lacks trusted service origin metadata");
        }
        LOGGER.info("INSPECTION_WORKER_AUDIT event=consumed principal=inspection-worker role=InspectionWorker origin=handling-event-service correlation=" + correlationId);
    }

    private boolean isCanonicalUuid(String value) {
        if (value == null) return false;
        try {
            return UUID.fromString(value).toString().equals(value);
        } catch (IllegalArgumentException invalid) {
            return false;
        }
    }
}
