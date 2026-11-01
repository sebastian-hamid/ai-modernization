package net.java.cargotracker.interfaces.security;
import jakarta.servlet.*;import jakarta.servlet.http.*;
import java.io.IOException;import java.nio.charset.StandardCharsets;import java.util.*;
/** Only the routing endpoint accepts a native realm service credential via Basic. */
public class RoutingAuthenticationFilter implements Filter {
    private static final String ROUTE="/rest/graph-traversal/shortest-path";
    @Override public void doFilter(ServletRequest request,ServletResponse response,FilterChain chain)throws IOException,ServletException {
        HttpServletRequest req=(HttpServletRequest)request;HttpServletResponse res=(HttpServletResponse)response;
        String path=req.getRequestURI().substring(req.getContextPath().length());
        String header=req.getHeader("Authorization");
        if(!path.equals(ROUTE) || header==null){chain.doFilter(req,res);return;}
        res.setHeader("Cache-Control","no-store");
        if(req.getUserPrincipal()!=null){res.sendError(400);return;}
        if(Collections.list(req.getHeaders("Authorization")).size()!=1 || header.length()>2048 || !header.startsWith("Basic ")){res.sendError(401);return;}
        String decoded;
        try{decoded=new String(Base64.getDecoder().decode(header.substring(6)),StandardCharsets.UTF_8);}
        catch(IllegalArgumentException invalid){res.sendError(401);return;}
        int separator=decoded.indexOf(':');
        if(separator<1 || separator>128 || decoded.length()-separator-1<1 || decoded.length()-separator-1>1024){res.sendError(401);return;}
        boolean authenticated=false;
        try {
            try{req.login(decoded.substring(0,separator),decoded.substring(separator+1));authenticated=true;}
            catch(ServletException invalid){res.sendError(401);return;}
            if(!req.isUserInRole("RoutingService")){res.sendError(403);return;}
            chain.doFilter(req,res);
        }finally{
            if(authenticated){
                HttpSession session=req.getSession(false);
                try{req.logout();}finally{if(session!=null)try{session.invalidate();}catch(IllegalStateException alreadyInvalidated){/* no retained session */}}
            }
        }
    }
}
