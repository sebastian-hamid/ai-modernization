package lab.spike;
import jakarta.ejb.Stateless;
import jakarta.annotation.security.PermitAll;
import jakarta.persistence.PersistenceContext;
import jakarta.persistence.EntityManager;
import jakarta.inject.Inject;
import jakarta.jms.JMSContext;
import jakarta.jms.Queue;
import jakarta.annotation.Resource;
import java.util.UUID;
@Stateless @PermitAll
public class ProbeService {
    @PersistenceContext(unitName="SpikeUnit") EntityManager em;
    @Inject JMSContext messaging;
    @Resource(lookup="java:app/jms/ProbeQueue") Queue queue;
    public String create() {
        String id=UUID.randomUUID().toString();
        em.persist(new ProbeRecord(id));
        messaging.createProducer().send(queue,id);
        return id;
    }
    public ProbeRecord find(String id) { return em.find(ProbeRecord.class,id); }
    public long count() { return em.createQuery("select count(p) from ProbeRecord p",Long.class).getSingleResult(); }
    public void markMessage(String id) { updateFlag("messageSeen",id); }
    public void markBatch(String id) { updateFlag("batchSeen",id); }
    private void updateFlag(String field,String id) {
        // Each concurrent worker updates only its own flag, avoiding lost updates.
        int changed=em.createQuery("update ProbeRecord p set p."+field+"=true where p.id=:id")
            .setParameter("id",id).executeUpdate();
        if(changed!=1) throw new IllegalStateException("Missing persisted probe record");
    }
}
