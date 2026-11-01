package lab.spike;
import jakarta.ejb.ActivationConfigProperty;
import jakarta.ejb.MessageDriven;
import jakarta.inject.Inject;
import jakarta.jms.Message;
import jakarta.jms.MessageListener;
import jakarta.jms.JMSException;
@MessageDriven(activationConfig={
    @ActivationConfigProperty(propertyName="destinationType",propertyValue="jakarta.jms.Queue"),
    @ActivationConfigProperty(propertyName="destinationLookup",propertyValue="java:app/jms/ProbeQueue")})
public class ProbeConsumer implements MessageListener {
    @Inject ProbeService service;
    public void onMessage(Message message) {
        try { service.markMessage(message.getBody(String.class)); }
        catch(JMSException e) { throw new IllegalStateException(e); }
    }
}

