package lab.modernization.fixture;
import jakarta.enterprise.context.ApplicationScoped;
import lab.modernization.security.RequiresRoles;
import java.util.concurrent.atomic.AtomicInteger;
@ApplicationScoped
public class FixtureService {
    private final AtomicInteger effects=new AtomicInteger();
    @RequiresRoles({"Reader","Operator","Administrator"})
    public int count(){return effects.get();}
    @RequiresRoles({"Operator","Administrator"})
    public void operate(){effects.incrementAndGet();}
    @RequiresRoles({"Administrator"})
    public void administer(){effects.incrementAndGet();}
}
