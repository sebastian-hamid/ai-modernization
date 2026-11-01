package lab.spike;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
@Entity @Table(name="capability_probe")
public class ProbeRecord {
    @Id public String id;
    public boolean messageSeen;
    public boolean batchSeen;
    public ProbeRecord() {}
    public ProbeRecord(String id) { this.id=id; }
}

