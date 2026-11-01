package net.java.cargotracker.interfaces.security;
import jakarta.servlet.*;import jakarta.servlet.http.*;import java.io.*;import java.util.*;
public class ResourcePolicyFilter implements Filter {
    private static final Map<String,String> SAFE=Map.of(
        "/jakarta.faces.resource/faces.js.xhtml","jakarta.faces",
        "/jakarta.faces.resource/primeicons/primeicons.css.xhtml","primefaces",
        "/jakarta.faces.resource/primeicons/fonts/primeicons.woff2.xhtml","primefaces",
        "/jakarta.faces.resource/locales/locale-en.js.xhtml","primefaces",
        "/jakarta.faces.resource/components.css.xhtml","primefaces",
        "/jakarta.faces.resource/components.js.xhtml","primefaces",
        "/jakarta.faces.resource/core.js.xhtml","primefaces",
        "/jakarta.faces.resource/jquery/jquery.js.xhtml","primefaces",
        "/jakarta.faces.resource/jquery/jquery-plugins.js.xhtml","primefaces");
    @Override public void doFilter(ServletRequest request,ServletResponse response,FilterChain chain)throws IOException,ServletException{
        HttpServletRequest req=(HttpServletRequest)request;HttpServletResponse res=(HttpServletResponse)response;
        String path=req.getRequestURI().substring(req.getContextPath().length());
        if(path.startsWith("/jakarta.faces.resource/")){
            String library=SAFE.get(path);
            if(library==null || !Set.of("GET","HEAD").contains(req.getMethod()) || req.getParameterValues("ln")==null || req.getParameterValues("ln").length!=1 || !library.equals(req.getParameter("ln")) || !Set.of("ln","v").containsAll(req.getParameterMap().keySet())){res.sendError(404);return;}
        }
        chain.doFilter(req,res);
    }
}
