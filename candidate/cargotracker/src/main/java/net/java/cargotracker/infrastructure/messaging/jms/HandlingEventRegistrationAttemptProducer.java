package net.java.cargotracker.infrastructure.messaging.jms;

import jakarta.annotation.Resource;
import jakarta.ejb.EJB;
import jakarta.jms.JMSException;
import java.util.UUID;
import net.java.cargotracker.infrastructure.quarantine.HandlingRequestIdempotencyService;
import jakarta.annotation.security.RolesAllowed;
import jakarta.ejb.Stateless;
import jakarta.inject.Inject;
import jakarta.jms.Destination;
import jakarta.jms.JMSContext;
import net.java.cargotracker.interfaces.handling.HandlingEventRegistrationAttempt;

/** Publishes validated application attempts under a broker-scoped identity. */
@Stateless
@jakarta.annotation.security.RunAs("HandlingAttemptProducer")
@RolesAllowed({"Operator", "Administrator", "BatchWorker"})
public class HandlingEventRegistrationAttemptProducer {
    @Inject
    private JMSContext jmsContext;

    @Resource(lookup = "java:app/jms/HandlingEventRegistrationAttemptQueue")
    private Destination handlingEventQueue;
    @EJB
    private HandlingRequestIdempotencyService idempotencyService;

    public void publish(HandlingEventRegistrationAttempt attempt) {
        publish(attempt, UUID.randomUUID().toString());
    }

    public void publish(HandlingEventRegistrationAttempt attempt, String requestId) {
        if (!idempotencyService.reserve(requestId, attempt)) return;
        send(attempt, requestId);
    }

    @jakarta.annotation.security.RolesAllowed("Administrator")
    public void publishReplay(HandlingEventRegistrationAttempt attempt, String requestId) {
        send(attempt, requestId);
    }

    private void send(HandlingEventRegistrationAttempt attempt, String requestId) {
        try {
            jakarta.jms.ObjectMessage message = jmsContext.createObjectMessage(attempt);
            message.setStringProperty("handlingRequestId", requestId);
            message.setStringProperty("handlingQuarantineMessageKey", UUID.randomUUID().toString());
            jmsContext.createProducer()
                    .setPriority(0)
                    .setDisableMessageID(true)
                    .setDisableMessageTimestamp(true)
                    .setTimeToLive(HandlingAttemptConfiguration.timeToLiveMillis())
                    .send(handlingEventQueue, message);
        } catch (JMSException failure) {
            throw new IllegalStateException("Handling attempt could not be enqueued", failure);
        }
    }
}
