package net.java.cargotracker.infrastructure.messaging.jms;

import jakarta.annotation.Resource;
import jakarta.annotation.security.RolesAllowed;
import jakarta.ejb.SessionContext;
import jakarta.ejb.Stateless;
import java.util.Set;
import java.util.logging.Logger;

/** Verifies server worker identity and emits identifier-free notification audit entries. */
@Stateless
@RolesAllowed("NotificationWorker")
public class NotificationWorkerAudit {
    private static final Logger LOGGER = Logger.getLogger(NotificationWorkerAudit.class.getName());
    private static final Set<String> EVENTS = Set.of("delivered", "misdirected", "rejected-registration");

    @Resource
    private SessionContext sessionContext;

    public void recordConsumed(String event) {
        String principal = sessionContext.getCallerPrincipal().getName();
        if (!"notification-worker".equals(principal)
                || !sessionContext.isCallerInRole("NotificationWorker")) {
            throw new SecurityException("Notification consumer lacks its dedicated worker identity");
        }
        if (!EVENTS.contains(event)) {
            throw new SecurityException("Unknown notification audit event");
        }
        LOGGER.info("NOTIFICATION_WORKER_AUDIT event=consumed consumer=" + event
                + " principal=notification-worker role=NotificationWorker");
    }
}
