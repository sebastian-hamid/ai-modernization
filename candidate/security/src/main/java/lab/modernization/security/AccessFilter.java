package lab.modernization.security;
import jakarta.servlet.*;import jakarta.servlet.http.*;
import java.io.*;import java.util.*;

/** Explicit route permissions; unknown routes denied before downstream execution. */
public class AccessFilter implements Filter {
    private final Map<String,Set<String>> routes=new HashMap<>();
    private final Set<String> publicRoutes=new HashSet<>();
    @Override public void init(FilterConfig config)throws ServletException {
        // Format: exact context-relative path TAB comma-separated roles or PUBLIC.
        try(BufferedReader reader=new BufferedReader(new InputStreamReader(
                Objects.requireNonNull(config.getServletContext().getResourceAsStream("/WEB-INF/access-routes.tsv")),"UTF-8"))) {
            for(String line;(line=reader.readLine())!=null;) {
                if(line.isBlank() || line.startsWith("#"))continue;
                String[] parts=line.split("\\t",-1);
                if(parts.length!=2 || !parts[0].startsWith("/") || routes.containsKey(parts[0]) || publicRoutes.contains(parts[0]))throw new ServletException("Invalid access manifest");
                if(parts[1].equals("PUBLIC"))publicRoutes.add(parts[0]);
                else routes.put(parts[0],Set.of(parts[1].split(",")));
            }
        }catch(IOException|NullPointerException failure){throw new ServletException("Missing access manifest",failure);}
    }
    @Override public void doFilter(ServletRequest request,ServletResponse response,FilterChain chain)throws IOException,ServletException {
        HttpServletRequest req=(HttpServletRequest)request;HttpServletResponse res=(HttpServletResponse)response;
        res.setHeader("Cache-Control","no-store");
        res.setHeader("X-Content-Type-Options","nosniff");
        String path=req.getRequestURI().substring(req.getContextPath().length());
        // Reject ambiguous representations instead of letting policy and container normalize differently.
        if(path.contains("%") || path.contains(";") || path.contains("//") || path.contains("/.") || path.contains("\\")){res.sendError(404);return;}
        if(publicRoutes.contains(path)) {chain.doFilter(req,res);return;}
        Set<String> roles=routes.get(path);
        if(roles==null){res.sendError(404);return;}
        if(req.getUserPrincipal()==null) {
            if(path.endsWith(".xhtml")) {res.setStatus(303);res.setHeader("Location",req.getContextPath()+"/login");}
            else res.sendError(401);
            return;
        }
        if(roles.stream().noneMatch(req::isUserInRole)){res.sendError(403);return;}
        if(!Set.of("GET","HEAD","OPTIONS").contains(req.getMethod()) && !SessionTokens.valid(req)){res.sendError(403);return;}
        chain.doFilter(req,res);
    }
}
