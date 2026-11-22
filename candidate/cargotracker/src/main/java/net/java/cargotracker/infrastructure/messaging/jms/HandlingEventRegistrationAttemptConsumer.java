package net.java.cargotracker.infrastructure.messaging.jms;

import jakarta.ejb.ActivationConfigProperty;
import jakarta.ejb.MessageDriven;
import jakarta.inject.Inject;
import jakarta.ejb.EJB;
import jakarta.jms.JMSException;
import jakarta.jms.Message;
import jakarta.jms.MessageListener;
import jakarta.jms.ObjectMessage;
import net.java.cargotracker.infrastructure.quarantine.HandlingQuarantineMessageKey;
import net.java.cargotracker.infrastructure.quarantine.HandlingRequestIdempotencyService;
import net.java.cargotracker.application.HandlingEventService;
import net.java.cargotracker.domain.model.handling.CannotCreateHandlingEventException;
import net.java.cargotracker.interfaces.handling.HandlingEventRegistrationAttempt;

/**
 * Consumes handling event registration attempt messages and delegates to proper
 * registration.
 */
@jakarta.annotation.security.RunAs("HandlingWorker")
@MessageDriven(activationConfig = {
    @ActivationConfigProperty(propertyName = "destinationType",
            propertyValue = "jakarta.jms.Queue"),
    @ActivationConfigProperty(propertyName = "destinationLookup",
            propertyValue = "java:app/jms/HandlingEventRegistrationAttemptQueue")
})
public class HandlingEventRegistrationAttemptConsumer implements MessageListener {

    @Inject
    private HandlingEventService handlingEventService;
    @EJB
    private HandlingWorkerAudit workerAudit;
    @EJB
    private HandlingRequestIdempotencyService idempotencyService;
//    private static final Logger logger = Logger.getLogger(
//            HandlingEventRegistrationAttemptConsumer.class.getName());

    @jakarta.annotation.security.PermitAll
    @Override
    public void onMessage(Message message) {
        try {
            ObjectMessage objectMessage = (ObjectMessage) message;
            HandlingEventRegistrationAttempt attempt
                    = (HandlingEventRegistrationAttempt) objectMessage.getObject();
            String requestId = message.getStringProperty("handlingRequestId");
            if (requestId == null) {
                // Compatibility for durable messages produced before request IDs were added.
                requestId = HandlingQuarantineMessageKey.legacyRequestId(message.getJMSMessageID(), attempt);
                idempotencyService.reserve(requestId, attempt);
            }
            if (!idempotencyService.beginProcessing(requestId, attempt)) return;
            workerAudit.recordConsumedAttempt();
            handlingEventService.registerHandlingEvent(
                    attempt.getCompletionTime(),
                    attempt.getTrackingId(),
                    attempt.getVoyageNumber(),
                    attempt.getUnLocode(),
                    attempt.getType());
            idempotencyService.markProcessed(requestId);
        } catch (CannotCreateHandlingEventException rejected) {
            // The broker routes bounded repeated failures to the sanitized rejection queue.
            // Do not attach the rejected DTO or nested validation text to server logs.
            throw new RuntimeException("Handling registration rejected by validation");
        } catch (JMSException unreadable) {
            // Broker retry/dead-letter handling owns final disposition for unreadable messages.
            throw new RuntimeException("Handling registration message could not be read");
        }
    }
}
