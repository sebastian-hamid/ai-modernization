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
            propertyValue = "java:app/jms/MisdirectedCargoQueue")
})
public class MisdirectedCargoConsumer implements MessageListener {

    @EJB
    private NotificationWorkerAudit workerAudit;

    @jakarta.annotation.security.PermitAll
    @Override
    public void onMessage(Message message) {
        try {
            workerAudit.recordConsumed("misdirected");
            message.getBody(String.class);
        } catch (JMSException ex) {
            java.util.logging.Logger.getLogger(MisdirectedCargoConsumer.class.getName())
                    .warning("Misdirected cargo notification could not be read.");
        }
    }
}
