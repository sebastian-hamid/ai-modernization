package net.java.cargotracker.infrastructure.messaging.jms;

import java.util.logging.Level;
import java.util.logging.Logger;
import jakarta.ejb.ActivationConfigProperty;
import jakarta.ejb.MessageDriven;
import jakarta.ejb.EJB;
import jakarta.inject.Inject;
import jakarta.jms.JMSException;
import jakarta.jms.Message;
import jakarta.jms.MessageListener;
import jakarta.jms.TextMessage;
import net.java.cargotracker.application.CargoInspectionService;
import net.java.cargotracker.domain.model.cargo.TrackingId;

/**
 * Consumes JMS messages and delegates notification of misdirected cargo to the
 * tracking service.
 *
 * This is a programmatic hook into the JMS infrastructure to make cargo
 * inspection message-driven.
 */
@jakarta.annotation.security.RunAs("InspectionWorker")
@MessageDriven(activationConfig = {
    @ActivationConfigProperty(propertyName = "destinationType",
        propertyValue = "jakarta.jms.Queue"),
    @ActivationConfigProperty(propertyName = "destinationLookup",
        propertyValue = "java:app/jms/CargoHandledQueue")
})
public class CargoHandledConsumer implements MessageListener {

    @Inject
    private CargoInspectionService cargoInspectionService;
    @EJB
    private InspectionWorkerAudit workerAudit;
    private static final Logger logger = Logger.getLogger(
            CargoHandledConsumer.class.getName());

    @jakarta.annotation.security.PermitAll
    @Override
    public void onMessage(Message message) {
        try {
            TextMessage textMessage = (TextMessage) message;
            String trackingIdString = textMessage.getText();
            workerAudit.recordConsumedAttempt(
                    message.getJMSCorrelationID(),
                    message.getStringProperty("producerOrigin"));

            cargoInspectionService.inspectCargo(new TrackingId(trackingIdString));
        } catch (JMSException e) {
            logger.log(Level.SEVERE, "Error procesing JMS message", e);
        }
    }
}
