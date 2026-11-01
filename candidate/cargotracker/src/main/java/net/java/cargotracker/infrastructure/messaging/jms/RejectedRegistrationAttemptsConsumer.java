package net.java.cargotracker.infrastructure.messaging.jms;

import java.util.logging.Level;
import java.util.logging.Logger;
import jakarta.ejb.ActivationConfigProperty;
import jakarta.ejb.MessageDriven;
import jakarta.jms.JMSException;
import jakarta.jms.Message;
import jakarta.jms.MessageListener;

@MessageDriven(activationConfig = {
    @ActivationConfigProperty(propertyName = "destinationType",
            propertyValue = "jakarta.jms.Queue"),
    @ActivationConfigProperty(propertyName = "destinationLookup",
            propertyValue = "java:app/jms/RejectedRegistrationAttemptsQueue")
})
public class RejectedRegistrationAttemptsConsumer implements MessageListener {

    private static final Logger logger = Logger.getLogger(
            RejectedRegistrationAttemptsConsumer.class.getName());

    @Override
    public void onMessage(Message message) {
        try {
            logger.log(Level.INFO,
                    "Rejected registration attempt of cargo with tracking ID {0}.",
                    message.getBody(String.class));
        } catch (JMSException ex) {
            logger.log(Level.WARNING, "Error processing message.", ex);
        }
    }
}
