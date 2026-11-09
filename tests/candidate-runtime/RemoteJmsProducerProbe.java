package lab.fixture;

import jakarta.jms.ConnectionFactory;
import jakarta.jms.JMSContext;
import jakarta.jms.JMSRuntimeException;
import jakarta.jms.Queue;
import javax.naming.Context;
import javax.naming.InitialContext;
import javax.naming.NamingException;
import java.io.FileInputStream;
import java.util.Date;
import java.util.Hashtable;
import java.util.Properties;
import net.java.cargotracker.domain.model.cargo.TrackingId;
import net.java.cargotracker.domain.model.handling.HandlingEvent;
import net.java.cargotracker.domain.model.location.UnLocode;
import net.java.cargotracker.interfaces.handling.HandlingEventRegistrationAttempt;

/** Separate-JVM probe for broker authentication and destination permissions. */
public final class RemoteJmsProducerProbe {
    private static final String FACTORY = "jms/RemoteConnectionFactory";
    private static final String ATTEMPT = "HandlingEventRegistrationAttemptQueue";
    private static final String REJECTED = "RejectedRegistrationAttemptsQueue";
    private static final String DELIVERED = "DeliveredCargoQueue";

    private static InitialContext lookupContext(String user, String password) throws NamingException {
        Hashtable<String, Object> env = new Hashtable<>();
        env.put(Context.INITIAL_CONTEXT_FACTORY, "org.wildfly.naming.client.WildFlyInitialContextFactory");
        env.put(Context.PROVIDER_URL, "remote+http://127.0.0.1:8080");
        if (user != null) {
            env.put(Context.SECURITY_PRINCIPAL, user);
            env.put(Context.SECURITY_CREDENTIALS, password);
        }
        return new InitialContext(env);
    }

    private static boolean deniedSend(String user, String password, String address) {
        InitialContext naming = null;
        JMSContext context = null;
        try {
            naming = lookupContext(user, password);
            ConnectionFactory factory = (ConnectionFactory) naming.lookup(FACTORY);
            context = user == null ? factory.createContext(JMSContext.AUTO_ACKNOWLEDGE)
                    : factory.createContext(user, password, JMSContext.AUTO_ACKNOWLEDGE);
            Queue queue = context.createQueue(address);
            context.createProducer().send(queue, context.createTextMessage("unauthorized boundary probe"));
            return false;
        } catch (NamingException | JMSRuntimeException | SecurityException denied) {
            return true;
        } finally {
            if (context != null) context.close();
            if (naming != null) {
                try { naming.close(); } catch (NamingException ignored) { }
            }
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("private credentials file required");
        Properties credentials = new Properties();
        try (FileInputStream input = new FileInputStream(args[0])) { credentials.load(input); }
        String producer = credentials.getProperty("producer.user");
        String producerPassword = credentials.getProperty("producer.password");
        ConnectionFactory factory;
        InitialContext trustedLookup = lookupContext(producer, producerPassword);
        factory = (ConnectionFactory) trustedLookup.lookup(FACTORY);
        trustedLookup.close();

        String[] humanUsers = {"reader", "operator", "admin"};
        boolean[] humanAuthenticated = new boolean[humanUsers.length];
        boolean[] humanSendDenied = new boolean[humanUsers.length];
        for (int i = 0; i < humanUsers.length; i++) {
            String user = humanUsers[i];
            String password = credentials.getProperty(user + ".password");
            InitialContext humanLookup = lookupContext(user, password);
            humanLookup.lookup(FACTORY);
            humanLookup.close();
            humanAuthenticated[i] = true;
            humanSendDenied[i] = deniedSend(user, password, ATTEMPT);
        }
        boolean anonymousDenied;
        try {
            InitialContext anonymousLookup = lookupContext(null, null);
            anonymousLookup.lookup(FACTORY);
            anonymousLookup.close();
            anonymousDenied = deniedSend(null, null, ATTEMPT);
        } catch (NamingException | JMSRuntimeException denied) {
            anonymousDenied = true;
        }

        boolean trustedAllowed;
        InitialContext producerLookup = lookupContext(producer, producerPassword);
        producerLookup.lookup(FACTORY);
        producerLookup.close();
        try (JMSContext context = factory.createContext(producer, producerPassword, JMSContext.AUTO_ACKNOWLEDGE)) {
            Queue queue = context.createQueue(ATTEMPT);
            Date now = new Date();
            HandlingEventRegistrationAttempt attempt = new HandlingEventRegistrationAttempt(
                    now, now, new TrackingId("NOCARGO1"), null, HandlingEvent.Type.RECEIVE,
                    new UnLocode("USCHI"));
            context.createProducer().send(queue, context.createObjectMessage(attempt));
            trustedAllowed = true;
        }
        boolean rejectedQueueDenied = deniedSend(producer, producerPassword, REJECTED);
        boolean deliveredQueueDenied = deniedSend(producer, producerPassword, DELIVERED);
        System.out.println("{\"anonymousDenied\":" + anonymousDenied
                + ",\"humanAuthenticated\":[" + humanAuthenticated[0] + "," + humanAuthenticated[1] + "," + humanAuthenticated[2] + "]"
                + ",\"humanSendDenied\":[" + humanSendDenied[0] + "," + humanSendDenied[1] + "," + humanSendDenied[2] + "]"
                + ",\"trustedAllowed\":" + trustedAllowed
                + ",\"rejectedQueueDenied\":" + rejectedQueueDenied
                + ",\"deliveredQueueDenied\":" + deliveredQueueDenied + "}");
        if (!anonymousDenied || !trustedAllowed || !rejectedQueueDenied || !deliveredQueueDenied) System.exit(2);
        for (int i = 0; i < humanUsers.length; i++) {
            if (!humanAuthenticated[i] || !humanSendDenied[i]) System.exit(3);
        }
    }
}
