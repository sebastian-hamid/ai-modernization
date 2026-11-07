package lab.fixture;
public interface LabEffectsMBean {
 String getSnapshot() throws Exception;
 String inspectHandlingEvent(String trackingId,String completionDate,String locationCode) throws Exception;
}
