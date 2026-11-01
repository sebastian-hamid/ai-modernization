package lab.fixture;
import jakarta.interceptor.*;import java.util.concurrent.*;import java.util.concurrent.atomic.*;
public class InvocationAudit {
 public static final ConcurrentMap<String,AtomicLong> COUNTS=new ConcurrentHashMap<>();
 @AroundInvoke public Object audit(InvocationContext context)throws Exception {
  String key=context.getMethod().getDeclaringClass().getName()+"#"+context.getMethod().getName();
  COUNTS.computeIfAbsent(key,ignored->new AtomicLong()).incrementAndGet();
  return context.proceed();
 }
}
