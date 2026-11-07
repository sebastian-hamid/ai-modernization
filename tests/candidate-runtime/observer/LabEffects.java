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
 @Override public String inspectHandlingEvent(String trackingId,String completionDate,String locationCode)throws Exception {
  if(trackingId==null||!trackingId.matches("[A-Z0-9]{8}")||!"2032-02-04".equals(completionDate)||!Set.of("USCHI","DEHAM").contains(locationCode))
   throw new IllegalArgumentException("Invalid bounded event observation selector");
  JsonArrayBuilder matches=Json.createArrayBuilder();int count=0;
  String sql="SELECT c.tracking_id AS TRACKING_ID,h.type AS EVENT_TYPE,h.completionTime AS COMPLETION_TIME,l.unlocode AS LOCATION_CODE,v.voyage_number AS VOYAGE_NUMBER "+
   "FROM HANDLINGEVENT h JOIN CARGO c ON c.id=h.cargo_id JOIN LOCATION l ON l.id=h.location_id LEFT JOIN VOYAGE v ON v.id=h.voyage_id "+
   "WHERE c.tracking_id=? AND h.completionTime=? AND l.unlocode=? AND h.type='CUSTOMS'";
  try(Connection c=dataSource.getConnection();PreparedStatement q=c.prepareStatement(sql)){
   c.setReadOnly(true);q.setString(1,trackingId);q.setDate(2,java.sql.Date.valueOf(completionDate));q.setString(3,locationCode);
   try(ResultSet rows=q.executeQuery()){
    while(rows.next()){
     count++;JsonObjectBuilder row=Json.createObjectBuilder().add("tracking_id",rows.getString("TRACKING_ID"))
      .add("event_type",rows.getString("EVENT_TYPE")).add("completion_time",rows.getDate("COMPLETION_TIME").toLocalDate().atStartOfDay().format(java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss")))
      .add("location_code",rows.getString("LOCATION_CODE"));
     String voyage=rows.getString("VOYAGE_NUMBER");if(voyage==null)row.addNull("voyage_number");else row.add("voyage_number",voyage);
     matches.add(row);
    }
   }
  }
  return Json.createObjectBuilder().add("row_count",count).add("matches",matches).build().toString();
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
  return Json.createObjectBuilder().add("tables",tables).add("queues",queues).add("business_invocations",calls).add("routing_identity",RoutingIdentityFilter.LAST.get()).build().toString();
 }
}
