package lab.fixture;

import jakarta.jms.ConnectionFactory;
import jakarta.jms.JMSContext;
import jakarta.jms.JMSException;
import javax.naming.Context;
import javax.naming.InitialContext;
import javax.naming.NameClassPair;
import javax.naming.NamingEnumeration;
import javax.naming.NamingException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Hashtable;
import java.util.Properties;
import java.io.FileInputStream;

/** Read-only protocol probe; looks up and opens a JMS connection but sends/consumes nothing. */
public final class RemoteJndiReachabilityProbe {
    private static final String FACTORY = "jms/RemoteConnectionFactory";

    private static boolean authenticationDenial(Throwable error) {
        for (Throwable current=error; current!=null; current=current.getCause()) {
            String type=current.getClass().getName().toLowerCase(java.util.Locale.ROOT);
            String message=current.getMessage();
            String normalized=message==null?"":message.toLowerCase(java.util.Locale.ROOT);
            if (type.contains("authenticationexception") || type.contains("sasl")
                    || type.contains("securityexception") || type.contains("notauthorized")
                    || type.contains("jms") && type.contains("security")
                    || type.contains("activemqsecurity")
                    || type.contains("nopermissionexception")
                    || type.contains("accesscontrolexception")
                    || type.contains("authorizationexception")
                    || type.contains("forbiddenexception")
                    || normalized.contains("authentication failed")
                    || normalized.contains("unable to validate user")
                    || normalized.contains("not authorized")
                    || normalized.contains("not authorised")
                    || normalized.contains("permission denied")
                    || message!=null && (message.contains("AMQ229031") || message.contains("AMQ229032"))) return true;
            if (current instanceof JMSException jms && jms.getLinkedException()!=null
                    && jms.getLinkedException()!=current.getCause()
                    && authenticationDenial(jms.getLinkedException())) return true;
        }
        return false;
    }

    private static void listExported(Context context, String prefix, int depth, List<String> entries)
            throws NamingException {
        if (depth > 8 || entries.size() > 100) throw new NamingException("Exported naming tree exceeded probe bounds");
        NamingEnumeration<NameClassPair> names=context.list("");
        try {
            while (names.hasMore()) {
                NameClassPair pair=names.next();
                String name=prefix.isEmpty()?pair.getName():prefix+"/"+pair.getName();
                String type=pair.getClassName()==null?"":pair.getClassName();
                entries.add(name+"="+type);
                if ("jms".equals(name) || type.endsWith("Context")) {
                    Object child=context.lookup(pair.getName());
                    if (child instanceof Context childContext) {
                        try { listExported(childContext,name,depth+1,entries); }
                        finally { childContext.close(); }
                    }
                }
            }
        } finally {
            names.close();
        }
    }

    private static void probe(String label, String provider, String user, String password) {
        InitialContext naming=null;
        JMSContext jms=null;
        boolean lookup=false;
        boolean started=false;
        boolean denied=false;
        boolean exportedListSucceeded=false;
        boolean seedGeneratorBinding=false;
        List<String> exportedBindings=new ArrayList<>();
        String failure="none";
        try {
            Hashtable<String,Object> env=new Hashtable<>();
            env.put(Context.INITIAL_CONTEXT_FACTORY,"org.wildfly.naming.client.WildFlyInitialContextFactory");
            env.put(Context.PROVIDER_URL,provider);
            if (user!=null) {
                env.put(Context.SECURITY_PRINCIPAL,user);
                env.put(Context.SECURITY_CREDENTIALS,password);
            }
            naming=new InitialContext(env);
            ConnectionFactory factory=(ConnectionFactory)naming.lookup(FACTORY);
            lookup=true;
            listExported(naming,"",0,exportedBindings);
            exportedListSucceeded=exportedBindings.stream().anyMatch(value -> value.startsWith("jms/RemoteConnectionFactory="));
            seedGeneratorBinding=exportedBindings.stream().anyMatch(value ->
                    value.toLowerCase(java.util.Locale.ROOT).contains("sampledatagenerator"));
            jms=user==null?factory.createContext():factory.createContext(user,password);
            jms.start();
            started=true;
        } catch (Throwable error) {
            denied=authenticationDenial(error);
            Throwable root=error;
            while (root.getCause()!=null && root.getCause()!=root) root=root.getCause();
            failure=root.getClass().getName();
        }
        boolean jmsClosed=true;
        boolean namingClosed=true;
        if (jms!=null) try { jms.close(); } catch (Throwable error) { jmsClosed=false; }
        if (naming!=null) try { naming.close(); } catch (Throwable error) { namingClosed=false; }
        String bindingBlob=Base64.getUrlEncoder().withoutPadding().encodeToString(
                String.join("\n",exportedBindings).getBytes(StandardCharsets.UTF_8));
        System.out.println("PROBE_RESULT "+label+" lookup="+lookup+" connection_started="+started
                +" authentication_denial="+denied+" jms_closed="+jmsClosed
                +" naming_closed="+namingClosed+" exported_list_succeeded="+exportedListSucceeded
                +" seed_generator_binding="+seedGeneratorBinding+" exported_bindings_b64="+bindingBlob
                +" failure="+failure);
    }

    public static void main(String[] args) throws Exception {
        if (args.length!=2) throw new IllegalArgumentException("provider URL and private credentials file required");
        Properties credentials=new Properties();
        try (FileInputStream input=new FileInputStream(args[1])) { credentials.load(input); }
        for (String user:new String[]{"reader","operator","admin"}) {
            probe(user,args[0],user,credentials.getProperty(user+".password"));
        }
        probe("anonymous",args[0],null,null);
        probe("invalid",args[0],"invalid-kan18-user","invalid-kan18-password");
    }
}
