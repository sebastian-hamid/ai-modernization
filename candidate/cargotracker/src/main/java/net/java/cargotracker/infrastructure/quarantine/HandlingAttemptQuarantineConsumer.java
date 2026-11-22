package net.java.cargotracker.infrastructure.quarantine;

import jakarta.ejb.EJB;
import jakarta.ejb.EJBException;
import jakarta.ejb.MessageDriven;
import jakarta.jms.JMSException;
import jakarta.jms.Message;
import jakarta.jms.MessageListener;
import jakarta.jms.ObjectMessage;
import java.util.logging.Logger;
import net.java.cargotracker.interfaces.handling.HandlingEventRegistrationAttempt;

/** Moves broker-expired attempts into the bounded PostgreSQL quarantine before acknowledging intake. */
@jakarta.annotation.security.RunAs("HandlingQuarantineWorker")
@MessageDriven(activationConfig = {
    @jakarta.ejb.ActivationConfigProperty(propertyName = "destinationType", propertyValue = "jakarta.jms.Queue"),
    @jakarta.ejb.ActivationConfigProperty(propertyName = "destinationLookup",
            propertyValue = "java:app/jms/HandlingAttemptQuarantineIntakeQueue")
})
public class HandlingAttemptQuarantineConsumer implements MessageListener {
    private static final Logger LOG = Logger.getLogger(HandlingAttemptQuarantineConsumer.class.getName());
    @EJB
    private HandlingAttemptQuarantineService quarantineService;
    @EJB
    private HandlingQuarantineCapacityAlert capacityAlert;

    @jakarta.annotation.security.PermitAll
    @Override
    public void onMessage(Message message) {
        try {
            if (!(message instanceof ObjectMessage objectMessage)) {
                throw new EJBException("Unexpected quarantine intake message type");
            }
            Object value = objectMessage.getObject();
            if (!(value instanceof HandlingEventRegistrationAttempt attempt)) {
                throw new EJBException("Unexpected quarantine intake payload type");
            }
            String messageKeyProperty = message.getStringProperty("handlingQuarantineMessageKey");
            String jmsMessageId = message.getJMSMessageID();
            String requestId = message.getStringProperty("handlingRequestId");
            if (requestId == null) {
                requestId = HandlingQuarantineMessageKey.legacyRequestId(jmsMessageId, attempt);
                quarantineService.registerLegacyRequest(requestId, attempt);
            }
            String messageKey = HandlingQuarantineMessageKey.from(messageKeyProperty, requestId, jmsMessageId);
            quarantineService.store(attempt, requestId, messageKey);
        } catch (QuarantineCapacityFullException full) {
            capacityAlert.full(full.requestId(), full.messageKey(), full.usedBytes(), full.messageBytes(), full.capacityBytes());
            // Container-managed MDB transactions roll back; unlimited queue redelivery keeps
            // this durable intake item pending until the quarantine has capacity again.
            throw new EJBException("Handling quarantine is full; intake remains pending", full);
        } catch (JMSException | EJBException failure) {
            LOG.warning("Handling quarantine intake could not be persisted; broker will retry.");
            throw new EJBException("Handling quarantine intake failed", failure);
        }
    }
}
