package net.java.cargotracker.interfaces.booking.socket;
import jakarta.servlet.*;import jakarta.servlet.http.*;import jakarta.inject.Inject;import java.io.*;import java.util.*;
public class SocketAccessFilter implements Filter {
    @Inject SocketSessions sessions;
    private Set<String> origins=Set.of();
    @Override public void init(FilterConfig config){String value=System.getProperty("cargo.websocket.allowed-origins","");origins=value.isBlank()?Set.of():Set.of(value.split(","));}
    @Override public void doFilter(ServletRequest request,ServletResponse response,FilterChain chain)throws IOException,ServletException{
        HttpServletRequest req=(HttpServletRequest)request;HttpServletResponse res=(HttpServletResponse)response;
        if(!req.getRequestURI().equals(req.getContextPath()+"/tracking")){chain.doFilter(req,res);return;}
        if(req.getUserPrincipal()==null){res.sendError(401);return;}
        if(!req.isUserInRole("Reader")&&!req.isUserInRole("Operator")&&!req.isUserInRole("Administrator")){res.sendError(403);return;}
        if(Collections.list(req.getHeaders("Origin")).size()!=1 || !origins.contains(req.getHeader("Origin"))){res.sendError(403);return;}
        String id=req.getParameter("connection");
        if(!"GET".equals(req.getMethod()) || !"websocket".equalsIgnoreCase(req.getHeader("Upgrade")) || id==null || !id.matches("[a-f0-9-]{36}") || req.getParameterValues("connection").length!=1 || req.getParameterMap().size()!=1){res.sendError(400);return;}
        HttpSession http=req.getSession(false);
        if(http==null || !sessions.reserve(id,http,req.getUserPrincipal().getName())){res.sendError(403);return;}
        chain.doFilter(req,res);
    }
}
