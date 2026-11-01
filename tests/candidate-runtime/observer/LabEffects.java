package lab.fixture;
import jakarta.interceptor.ExcludeDefaultInterceptors;import jakarta.annotation.*;import jakarta.ejb.*;import jakarta.json.*;
import javax.sql.DataSource;import javax.management.*;import java.lang.management.*;
import java.sql.*;import java.security.*;import java.nio.charset.StandardCharsets;import java.util.*;
@Singleton @Startup @ExcludeDefaultInterceptors
public class LabEffects implements LabEffectsMBean {
 @Resource(lookup="java:/jboss/datasources/ExampleDS") DataSource dataSource;
 private final MBeanServer server=ManagementFactory.getPlatformMBeanServer();
 private static final String[] ATTRIBUTES={"MessageCount","DeliveringCount","ScheduledCount","MessagesAdded","MessagesAcknowledged","MessagesExpired","MessagesKilled","AcknowledgeAttempts"};
 @PostConstruct void start()throws Exception {
  if(!Boolean.getBoolean("lab.candidate.disposable"))throw new IllegalStateException("Lab observer refuses non-disposable runtime");
  server.registerMBean(new StandardMBean(this,LabEffectsMBean.class),new ObjectName("lab.fixture:type=Effects"));
 }
 @PreDestroy void stop()throws Exception {server.unregisterMBean(new ObjectName("lab.fixture:type=Effects"));}
 private static String hash(String text)throws Exception {
  return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(text.getBytes(StandardCharsets.UTF_8)));
 }
 @Override public String getSnapshot()throws Exception {
  JsonObjectBuilder tables=Json.createObjectBuilder();
  int tableCount=0;long records=0;
  try(Connection c=dataSource.getConnection()){
   c.setReadOnly(true);
   try(ResultSet names=c.getMetaData().getTables(null,"PUBLIC","%",new String[]{"TABLE"})){
    while(names.next()){
     String name=names.getString("TABLE_NAME");List<String> rows=new ArrayList<>();
     // Database metadata names are quoted, never supplied by a caller.
     try(Statement query=c.createStatement();ResultSet data=query.executeQuery("SELECT * FROM \"PUBLIC\".\""+name.replace("\"","\"\"")+"\"")){
      int columns=data.getMetaData().getColumnCount();
      while(data.next()){
       JsonArrayBuilder row=Json.createArrayBuilder();
       for(int col=1;col<=columns;col++){String value=data.getString(col);if(value==null)row.addNull();else row.add(value);}
       rows.add(row.build().toString());
      }
     }
     Collections.sort(rows);records+=rows.size();tableCount++;
     tables.add(name,Json.createObjectBuilder().add("rows",rows.size()).add("sha256",hash(String.join("\n",rows))));
    }
   }
  }
  if(tableCount==0 || records==0)throw new IllegalStateException("Empty database observer");
  JsonObjectBuilder queues=Json.createObjectBuilder();Set<String> found=new HashSet<>();
  for(ObjectName name:new TreeSet<>(server.queryNames(new ObjectName("org.apache.activemq.artemis:*"),null))){
   if(!"queues".equals(name.getKeyProperty("subcomponent")))continue;
   String q=(String)server.getAttribute(name,"Name");found.add(q);
   server.invoke(name,"flushExecutor",new Object[0],new String[0]);
   JsonObjectBuilder counts=Json.createObjectBuilder();
   for(String attribute:ATTRIBUTES)counts.add(attribute,((Number)server.getAttribute(name,attribute)).longValue());
   queues.add(q,counts);
  }
  for(String required:List.of("HandlingEventRegistrationAttemptQueue","CargoHandledQueue","MisdirectedCargoQueue","DeliveredCargoQueue","RejectedRegistrationAttemptsQueue","DLQ","ExpiryQueue")){
   if(found.stream().noneMatch(q->q.endsWith(required)))throw new IllegalStateException("Missing queue observer: "+required);
  }
  JsonObjectBuilder calls=Json.createObjectBuilder();new TreeMap<>(InvocationAudit.COUNTS).forEach((key,value)->calls.add(key,value.get()));
  return Json.createObjectBuilder().add("tables",tables).add("queues",queues).add("business_invocations",calls).build().toString();
 }
}
