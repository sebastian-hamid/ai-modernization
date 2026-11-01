package lab.modernization.security;
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import java.io.IOException;

/** Container-managed credentials; no application password store. */
public class LocalLoginServlet extends HttpServlet {
    @Override protected void doGet(HttpServletRequest req,HttpServletResponse res)throws IOException {
        res.setHeader("Cache-Control","no-store");
        res.setContentType("text/html;charset=UTF-8");
        String csrf=SessionTokens.get(req.getSession(true));
        res.getWriter().write("<!doctype html><html><head><title>Sign in</title></head><body><form method='post'><label>Username <input name='username' autocomplete='username'></label><label>Password <input type='password' name='password' autocomplete='current-password'></label><input type='hidden' name='csrf' value='"+csrf+"'><button>Sign in</button></form></body></html>");
    }
    @Override protected void doPost(HttpServletRequest req,HttpServletResponse res)throws IOException {
        res.setHeader("Cache-Control","no-store");
        if(!SessionTokens.valid(req)){res.sendError(403);return;}
        if(req.getUserPrincipal()!=null){res.sendError(409);return;}
        String username=req.getParameter("username"),password=req.getParameter("password");
        if(username==null || password==null || username.length()>128 || password.length()>1024){res.sendError(401);return;}
        try {
            req.login(username,password);
            req.changeSessionId();
            req.getSession().removeAttribute(SessionTokens.KEY);
            SessionTokens.get(req.getSession());
            res.setStatus(303);res.setHeader("Location",req.getContextPath()+"/session");
        }catch(ServletException failure){res.sendError(401);}
    }
}
