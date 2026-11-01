package lab.modernization.security;
import jakarta.servlet.*;import jakarta.servlet.http.*;import java.io.IOException;
public class LocalLogoutServlet extends HttpServlet {
    @Override protected void doPost(HttpServletRequest req,HttpServletResponse res)throws IOException {
        res.setHeader("Cache-Control","no-store");
        if(req.getUserPrincipal()==null){res.sendError(401);return;}
        if(!SessionTokens.valid(req)){res.sendError(403);return;}
        try {req.logout();}catch(ServletException failure){res.sendError(500);return;}
        HttpSession session=req.getSession(false);if(session!=null)session.invalidate();
        res.setStatus(204);
    }
}
