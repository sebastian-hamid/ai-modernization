package net.java.cargotracker.interfaces.booking.socket;
import jakarta.servlet.annotation.WebListener;import jakarta.servlet.http.*;import jakarta.inject.Inject;
@WebListener
public class SocketSessionListener implements HttpSessionListener {
    @Inject SocketSessions sessions;
    @Override public void sessionDestroyed(HttpSessionEvent event){sessions.revoke(event.getSession());}
}
