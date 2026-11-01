package lab.modernization.security;
import jakarta.servlet.http.*;
import java.security.SecureRandom;
import java.util.Base64;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

public final class SessionTokens {
    private SessionTokens() {}
    public static final String KEY="security.csrf";
    public static String get(HttpSession session) {
        synchronized(session) {
            String token=(String)session.getAttribute(KEY);
            if(token==null) { byte[] bytes=new byte[32]; new SecureRandom().nextBytes(bytes);
                token=Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);session.setAttribute(KEY,token);}
            return token;
        }
    }
    public static boolean valid(HttpServletRequest request) {
        HttpSession session=request.getSession(false);
        if(session==null)return false;
        String expected=(String)session.getAttribute(KEY);
        String received=request.getHeader("X-CSRF-Token");
        if(received==null)received=request.getParameter("csrf");
        return expected!=null && received!=null && MessageDigest.isEqual(expected.getBytes(StandardCharsets.UTF_8),received.getBytes(StandardCharsets.UTF_8));
    }
}
