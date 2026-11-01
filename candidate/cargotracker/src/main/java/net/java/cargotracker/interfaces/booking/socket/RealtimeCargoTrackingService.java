package net.java.cargotracker.interfaces.booking.socket;

import java.io.IOException;
import java.io.StringWriter;
import java.io.Writer;
import java.util.HashSet;
import java.util.Set;
import java.util.logging.Level;
import java.util.logging.Logger;
import jakarta.ejb.Singleton;
import jakarta.enterprise.event.Observes;
import jakarta.json.Json;
import jakarta.json.stream.JsonGenerator;
import jakarta.websocket.OnClose;
import jakarta.websocket.OnOpen;
import jakarta.websocket.Session;
import jakarta.websocket.server.ServerEndpoint;
import net.java.cargotracker.infrastructure.events.cdi.CargoInspected;
import net.java.cargotracker.domain.model.cargo.Cargo;

/**
 * WebSocket service for tracking all cargoes in real time.
 *
 * @author Vijay Nair
 */
@Singleton
@ServerEndpoint("/tracking")
public class RealtimeCargoTrackingService {

    private static final Logger logger = Logger.getLogger(
            RealtimeCargoTrackingService.class.getName());

    @jakarta.inject.Inject private SocketSessions sessions;

    @OnOpen
    public void onOpen(final Session session) {
        // Infinite by default on GlassFish. We need this principally for WebLogic.
        session.setMaxIdleTimeout(5 * 60 * 1000);
        java.util.List<String> ids=session.getRequestParameterMap().get("connection");
        sessions.opened(ids==null || ids.size()!=1 ? "" : ids.get(0),session);
    }

    @OnClose
    public void onClose(final Session session) {
        sessions.closed(session);
    }

    public void onCargoInspected(@Observes @CargoInspected Cargo cargo) {
        sessions.publish(net.java.cargotracker.interfaces.booking.rest.CargoSnapshot.forSocket(cargo).toString());
    }
}
