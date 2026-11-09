package net.java.cargotracker.infrastructure.messaging.jms;

import jakarta.ejb.ActivationConfigProperty;
import jakarta.ejb.EJB;
import jakarta.ejb.MessageDriven;
import jakarta.jms.JMSException;
import jakarta.jms.Message;
import jakarta.jms.MessageListener;

@jakarta.annotation.security.RunAs("NotificationWorker")
@MessageDriven(activationConfig = {
    @ActivationConfigProperty(propertyName = "destinationType",
            propertyValue = "jakarta.jms.Queue"),
    @ActivationConfigProperty(propertyName = "destinationLookup",
            propertyValue = "java:app/jms/DeliveredCargoQueue")
})
public class DeliveredCargoConsumer implements MessageListener {

    @EJB
    private NotificationWorkerAudit workerAudit;

    @jakarta.annotation.security.PermitAll
    @Override
    public void onMessage(Message message) {
        try {
            workerAudit.recordConsumed("delivered");
            message.getBody(String.class);
        } catch (JMSException ex) {
            java.util.logging.Logger.getLogger(DeliveredCargoConsumer.class.getName())
                    .warning("Delivered cargo notification could not be read.");
        }
    }
}
