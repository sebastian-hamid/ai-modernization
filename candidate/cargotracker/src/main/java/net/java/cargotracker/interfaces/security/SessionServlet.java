package net.java.cargotracker.interfaces.security;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.*;
import jakarta.json.Json;
import lab.modernization.security.SessionTokens;
import java.io.IOException;
@WebServlet("/session")
public class SessionServlet extends HttpServlet {
    @Override protected void doGet(HttpServletRequest req,HttpServletResponse res)throws IOException {
        res.setContentType("application/json");
        var roles=Json.createArrayBuilder();
        for(String role:new String[]{"Reader","Operator","Administrator"})if(req.isUserInRole(role))roles.add(role);
        res.getWriter().print(Json.createObjectBuilder().add("principal",req.getUserPrincipal().getName()).add("roles",roles).add("csrf",SessionTokens.get(req.getSession())).build());
    }
}
