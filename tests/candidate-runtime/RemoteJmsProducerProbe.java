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

    private static boolean isSendAuthorizationDenial(Throwable failure) {
        for (Throwable current = failure; current != null; current = current.getCause()) {
            String type = current.getClass().getName();
            String message = current.getMessage();
            String normalized = message == null ? "" : message.toLowerCase(java.util.Locale.ROOT);
            boolean securityType = type.endsWith("JMSSecurityException")
                    || type.endsWith("JMSSecurityRuntimeException")
                    || type.endsWith("ActiveMQSecurityException")
                    || type.endsWith("ActiveMQNotAuthorizedException")
                    || current instanceof SecurityException;
            boolean sendPermission = normalized.contains("send")
                    && (normalized.contains("permission") || normalized.contains("not authorized"))
                    || message != null && message.contains("AMQ229032");
            if (securityType && sendPermission || message != null && message.contains("AMQ229032")) return true;
            if (current instanceof jakarta.jms.JMSException jms && jms.getLinkedException() != null
                    && jms.getLinkedException() != current.getCause()) {
                Throwable linked=jms.getLinkedException();
                String linkedType=linked.getClass().getName();
                String linkedMessage=linked.getMessage();
                String linkedNormalized=linkedMessage == null ? "" : linkedMessage.toLowerCase(java.util.Locale.ROOT);
                boolean linkedSecurity=linkedType.endsWith("JMSSecurityException")
                        || linkedType.endsWith("JMSSecurityRuntimeException")
                        || linkedType.endsWith("ActiveMQSecurityException")
                        || linkedType.endsWith("ActiveMQNotAuthorizedException")
                        || linked instanceof SecurityException;
                boolean linkedSend=linkedNormalized.contains("send")
                        && (linkedNormalized.contains("permission") || linkedNormalized.contains("not authorized"))
                        || linkedMessage != null && linkedMessage.contains("AMQ229032");
                if (linkedSecurity && linkedSend
                        || linkedMessage != null && linkedMessage.contains("AMQ229032")) return true;
            }
        }
        return false;
    }

    private static boolean isAuthenticationDenial(Throwable failure) {
        for (Throwable current = failure; current != null; current = current.getCause()) {
            String type=current.getClass().getName();
            String message=current.getMessage();
            if (type.endsWith("AuthenticationException")
                    || message != null && (message.contains("AMQ229031")
                        || message.toLowerCase(java.util.Locale.ROOT).contains("unable to validate user"))) return true;
            if (current instanceof jakarta.jms.JMSException jms && jms.getLinkedException() != null) {
                Throwable linked=jms.getLinkedException();
                String linkedType=linked.getClass().getName();
                String linkedMessage=linked.getMessage();
                if (linkedType.endsWith("AuthenticationException")
                        || linkedMessage != null && (linkedMessage.contains("AMQ229031")
                            || linkedMessage.toLowerCase(java.util.Locale.ROOT).contains("unable to validate user"))) return true;
            }
        }
        return false;
    }

    private static JMSContext authenticatedContext(ConnectionFactory factory, String user, String password) {
        JMSContext context = user == null
                ? factory.createContext(JMSContext.AUTO_ACKNOWLEDGE)
                : factory.createContext(user, password, JMSContext.AUTO_ACKNOWLEDGE);
        try {
            context.start(); // Force broker authentication before testing destination authorization.
            return context;
        } catch (JMSRuntimeException failure) {
            context.close();
            throw new IllegalStateException("JMS broker connection/authentication failed",failure);
        }
    }

    private static boolean sendDenied(JMSContext context, String address) {
        Queue queue = context.createQueue(address);
        try {
            context.createProducer().send(queue, context.createTextMessage("unauthorized boundary probe"));
            return false;
        } catch (JMSRuntimeException failure) {
            if (isSendAuthorizationDenial(failure)) return true;
            throw new IllegalStateException("Unexpected JMS send failure; not an authorization denial",failure);
        } catch (SecurityException failure) {
            if (isSendAuthorizationDenial(failure)) return true;
            throw failure;
        }
    }

    private static boolean deniedSend(ConnectionFactory factory, String user, String password, String address) {
        JMSContext context = authenticatedContext(factory,user,password);
        try {
            return sendDenied(context,address);
        } finally {
            context.close();
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
            ConnectionFactory humanFactory = (ConnectionFactory) humanLookup.lookup(FACTORY);
            humanLookup.close();
            humanSendDenied[i] = deniedSend(humanFactory,user,password,ATTEMPT);
            humanAuthenticated[i] = true;
        }
        // Authenticated worker and batch principals must not bypass the EJB producer.
        String[] machineUsers = {"batch-worker", "handling-worker", "inspection-worker", "notification-worker"};
        boolean[] machineAuthenticated = new boolean[machineUsers.length];
        boolean[] machineSendDenied = new boolean[machineUsers.length];
        for (int i = 0; i < machineUsers.length; i++) {
            String user = machineUsers[i];
            String password = credentials.getProperty(user + ".password");
            if (password == null) throw new IllegalArgumentException("missing private machine credential: " + user);
            InitialContext machineLookup = lookupContext(user, password);
            ConnectionFactory machineFactory = (ConnectionFactory) machineLookup.lookup(FACTORY);
            machineLookup.close();
            machineSendDenied[i] = deniedSend(machineFactory,user,password,ATTEMPT);
            machineAuthenticated[i] = true;
        }

        boolean anonymousDenied;
        try {
            anonymousDenied = deniedSend(factory,null,null,ATTEMPT);
        } catch (IllegalStateException | JMSRuntimeException failure) {
            if (isAuthenticationDenial(failure)) anonymousDenied = true;
            else throw failure;
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
        boolean rejectedQueueDenied = deniedSend(factory,producer,producerPassword,REJECTED);
        boolean deliveredQueueDenied = deniedSend(factory,producer,producerPassword,DELIVERED);
        System.out.println("{\"anonymousDenied\":" + anonymousDenied
                + ",\"humanAuthenticated\":[" + humanAuthenticated[0] + "," + humanAuthenticated[1] + "," + humanAuthenticated[2] + "]"
                + ",\"humanSendDenied\":[" + humanSendDenied[0] + "," + humanSendDenied[1] + "," + humanSendDenied[2] + "]"
                + ",\"machinePrincipals\":[\"batch-worker\",\"handling-worker\",\"inspection-worker\",\"notification-worker\"]"
                + ",\"machineAuthenticated\":[" + machineAuthenticated[0] + "," + machineAuthenticated[1] + "," + machineAuthenticated[2] + "," + machineAuthenticated[3] + "]"
                + ",\"machineSendDenied\":[" + machineSendDenied[0] + "," + machineSendDenied[1] + "," + machineSendDenied[2] + "," + machineSendDenied[3] + "]"
                + ",\"trustedAllowed\":" + trustedAllowed
                + ",\"rejectedQueueDenied\":" + rejectedQueueDenied
                + ",\"deliveredQueueDenied\":" + deliveredQueueDenied + "}");
        if (!anonymousDenied || !trustedAllowed || !rejectedQueueDenied || !deliveredQueueDenied) System.exit(2);
        for (int i = 0; i < humanUsers.length; i++) {
            if (!humanAuthenticated[i] || !humanSendDenied[i]) System.exit(3);
        }
        for (int i = 0; i < machineUsers.length; i++) {
            if (!machineAuthenticated[i] || !machineSendDenied[i]) System.exit(4);
        }
    }
}
