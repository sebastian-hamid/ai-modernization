package net.java.cargotracker.infrastructure.messaging.jms;

import jakarta.annotation.Resource;
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

    public void publish(HandlingEventRegistrationAttempt attempt) {
        jmsContext.createProducer()
                .setPriority(0)
                .setDisableMessageID(true)
                .setDisableMessageTimestamp(true)
                .setTimeToLive(30000)
                .send(handlingEventQueue, attempt);
    }
}
