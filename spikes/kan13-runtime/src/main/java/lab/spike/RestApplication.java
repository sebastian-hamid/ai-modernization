package lab.spike;
import jakarta.ws.rs.ApplicationPath;
import jakarta.ws.rs.core.Application;
import jakarta.jms.JMSDestinationDefinition;
@ApplicationPath("api")
@JMSDestinationDefinition(name="java:app/jms/ProbeQueue", interfaceName="jakarta.jms.Queue", destinationName="kan13ProbeQueue")
public class RestApplication extends Application {}

