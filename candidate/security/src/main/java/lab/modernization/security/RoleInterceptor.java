package lab.modernization.security;
import jakarta.interceptor.*;import jakarta.annotation.Priority;
import jakarta.inject.Inject;import jakarta.servlet.http.HttpServletRequest;
import jakarta.enterprise.context.ContextNotActiveException;
import java.util.Arrays;
@Interceptor @RequiresRoles @Priority(Interceptor.Priority.APPLICATION)
public class RoleInterceptor {
    @Inject HttpServletRequest request;
    @AroundInvoke public Object authorize(InvocationContext invocation)throws Exception {
        RequiresRoles policy=invocation.getMethod().getAnnotation(RequiresRoles.class);
        if(policy==null)policy=invocation.getTarget().getClass().getAnnotation(RequiresRoles.class);
        boolean permitted=false;
        if(policy!=null) {
            try { permitted=request.getUserPrincipal()!=null && Arrays.stream(policy.value()).anyMatch(request::isUserInRole); }
            catch(ContextNotActiveException|IllegalStateException unavailable) { permitted=false; }
        }
        if(!permitted)throw new SecurityException("Application role denied");
        return invocation.proceed();
    }
}
