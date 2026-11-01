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
            propertyValue = "java:app/jms/DeliveredCargoQueue")
})
public class DeliveredCargoConsumer implements MessageListener {

    private static final Logger logger = Logger.getLogger(
            DeliveredCargoConsumer.class.getName());

    @Override
    public void onMessage(Message message) {
        try {
            logger.log(Level.INFO,
                    "Cargo with tracking ID {0} delivered.",
                    message.getBody(String.class));
        } catch (JMSException ex) {
            logger.log(Level.WARNING, "Error processing message.", ex);
        }
    }
}
