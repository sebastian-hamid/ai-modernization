package lab.modernization.fixture;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.*;
import lab.modernization.security.SessionTokens;
import java.io.IOException;
import jakarta.inject.Inject;
/** Test-only counter; never production business evidence. */
@WebServlet(urlPatterns={"/public","/session","/read","/operate","/admin","/page.xhtml","/boundary"})
public class FixtureServlet extends HttpServlet {
    @Inject FixtureService service;
    protected void doGet(HttpServletRequest req,HttpServletResponse res)throws IOException {
        res.setContentType("text/plain;charset=UTF-8");
        if(req.getServletPath().equals("/public")) {res.getWriter().print("Public test page");return;}
        String role=req.isUserInRole("Administrator")?"Administrator":req.isUserInRole("Operator")?"Operator":"Reader";
        res.getWriter().print(req.getUserPrincipal().getName()+"|"+role+"|"+SessionTokens.get(req.getSession())+"|"+service.count());
    }
    protected void doPost(HttpServletRequest req,HttpServletResponse res)throws IOException {
        if(!req.getServletPath().equals("/operate") && !req.getServletPath().equals("/admin") && !req.getServletPath().equals("/boundary")){res.sendError(405);return;}
        try {if(req.getServletPath().equals("/admin"))service.administer();else service.operate();}
        catch(SecurityException denied){res.sendError(403);return;}
        res.setStatus(204);
    }
}
