package lab.fixture;
import jakarta.interceptor.*;import java.util.Set;import java.util.concurrent.*;import java.util.concurrent.atomic.*;
public class InvocationAudit {
 public static final ConcurrentMap<String,AtomicLong> COUNTS=new ConcurrentHashMap<>();
 private static final Set<String> PERIODIC_MAINTENANCE=Set.of(
  "net.java.cargotracker.infrastructure.quarantine.HandlingQuarantineRetentionJob#purgeExpired",
  "net.java.cargotracker.infrastructure.quarantine.HandlingAttemptQuarantineService#purgeExpired");
 @AroundInvoke public Object audit(InvocationContext context)throws Exception {
  String key=context.getMethod().getDeclaringClass().getName()+"#"+context.getMethod().getName();
  // The test observer measures business calls; this one-second maintenance job
  // must not make otherwise quiet snapshots appear continuously active.
  if(!PERIODIC_MAINTENANCE.contains(key))COUNTS.computeIfAbsent(key,ignored->new AtomicLong()).incrementAndGet();
  return context.proceed();
 }
}
