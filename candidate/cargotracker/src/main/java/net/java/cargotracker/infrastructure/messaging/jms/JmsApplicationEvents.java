package net.java.cargotracker.infrastructure.messaging.jms;

import java.io.Serializable;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.UUID;
import jakarta.annotation.Resource;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.jms.Destination;
import jakarta.jms.JMSContext;
import net.java.cargotracker.application.ApplicationEvents;
import net.java.cargotracker.domain.model.cargo.Cargo;
import net.java.cargotracker.domain.model.handling.HandlingEvent;
import net.java.cargotracker.interfaces.handling.HandlingEventRegistrationAttempt;

@ApplicationScoped
public class JmsApplicationEvents implements ApplicationEvents, Serializable {

    private static final int LOW_PRIORITY = 0;
    @Inject
    JMSContext jmsContext;
    @Resource(lookup = "java:app/jms/CargoHandledQueue")
    private Destination cargoHandledQueue;
    @Resource(lookup = "java:app/jms/MisdirectedCargoQueue")
    private Destination misdirectedCargoQueue;
    @Resource(lookup = "java:app/jms/DeliveredCargoQueue")
    private Destination deliveredCargoQueue;
    @Resource(lookup = "java:app/jms/HandlingEventRegistrationAttemptQueue")
    private Destination handlingEventQueue;
    private static final Logger logger = Logger.getLogger(
            JmsApplicationEvents.class.getName());

    @Override
    public void cargoWasHandled(HandlingEvent event) {
        Cargo cargo = event.getCargo();
        logger.log(Level.INFO, "Cargo was handled {0}", cargo);
        String correlationId = UUID.randomUUID().toString();
        jakarta.jms.TextMessage message = jmsContext.createTextMessage(
                cargo.getTrackingId().getIdString());
        try {
            message.setJMSCorrelationID(correlationId);
            message.setStringProperty("producerOrigin", "handling-event-service");
        } catch (jakarta.jms.JMSException e) {
            throw new IllegalStateException("Cannot mark trusted cargo-handling event", e);
        }
        jmsContext.createProducer()
                .setPriority(LOW_PRIORITY)
                .setDisableMessageID(true)
                .setDisableMessageTimestamp(true)
                .send(cargoHandledQueue, message);
    }

    @Override
    public void cargoWasMisdirected(Cargo cargo) {
        logger.log(Level.INFO, "Cargo was misdirected {0}", cargo);
        jmsContext.createProducer()
                .setPriority(LOW_PRIORITY)
                .setDisableMessageID(true)
                .setDisableMessageTimestamp(true)
                .send(misdirectedCargoQueue,
                        cargo.getTrackingId().getIdString());
    }

    @Override
    public void cargoHasArrived(Cargo cargo) {
        logger.log(Level.INFO, "Cargo has arrived {0}", cargo);
        jmsContext.createProducer()
                .setPriority(LOW_PRIORITY)
                .setDisableMessageID(true)
                .setDisableMessageTimestamp(true)
                .send(deliveredCargoQueue,
                        cargo.getTrackingId().getIdString());
    }

    @Override
    public void receivedHandlingEventRegistrationAttempt(
            HandlingEventRegistrationAttempt attempt) {
        logger.log(Level.INFO, "Received handling event registration attempt {0}",
                attempt);
        jmsContext.createProducer()
                .setPriority(LOW_PRIORITY)
                .setDisableMessageID(true)
                .setDisableMessageTimestamp(true)
                .setTimeToLive(1000)
                .send(handlingEventQueue, attempt);
    }
}
