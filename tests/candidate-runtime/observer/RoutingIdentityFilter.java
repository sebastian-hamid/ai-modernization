package lab.fixture;
import jakarta.servlet.*;import jakarta.servlet.annotation.WebFilter;import jakarta.servlet.http.*;
import jakarta.json.*;import java.io.IOException;import java.util.List;import java.util.concurrent.atomic.*;
/** Disposable observation only: native principal/roles, never Authorization or credentials. */
@WebFilter(urlPatterns="/rest/graph-traversal/shortest-path")
public class RoutingIdentityFilter implements Filter {
 public static final AtomicLong SEQUENCE=new AtomicLong();
 public static final AtomicReference<JsonObject> LAST=new AtomicReference<>(Json.createObjectBuilder().build());
 @Override public void doFilter(ServletRequest request,ServletResponse response,FilterChain chain)throws IOException,ServletException {
  if(!Boolean.getBoolean("lab.candidate.disposable"))throw new ServletException("Lab observation outside fixture");
  HttpServletRequest req=(HttpServletRequest)request;
  if(req.getUserPrincipal()==null)throw new ServletException("Missing native routing principal");
  JsonArrayBuilder roles=Json.createArrayBuilder();
  for(String role:List.of("Reader","Operator","Administrator","RoutingService"))if(req.isUserInRole(role))roles.add(role);
  LAST.set(Json.createObjectBuilder().add("sequence",SEQUENCE.incrementAndGet()).add("principal",req.getUserPrincipal().getName()).add("roles",roles).add("path",req.getRequestURI().substring(req.getContextPath().length())).build());
  chain.doFilter(request,response);
 }
}
