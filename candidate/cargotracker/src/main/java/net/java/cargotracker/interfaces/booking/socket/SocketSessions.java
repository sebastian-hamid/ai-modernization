package net.java.cargotracker.interfaces.booking.socket;
import jakarta.enterprise.context.ApplicationScoped;import jakarta.annotation.*;import jakarta.enterprise.concurrent.ManagedScheduledExecutorService;
import jakarta.servlet.http.HttpSession;import jakarta.websocket.*;import java.util.*;import java.util.concurrent.*;
@ApplicationScoped
public class SocketSessions {
    @Resource(lookup="java:comp/DefaultManagedScheduledExecutorService") ManagedScheduledExecutorService executor;
    private final Map<String,Binding> pending=new ConcurrentHashMap<>(),active=new ConcurrentHashMap<>();
    private ScheduledFuture<?> timer;
    static class Binding {
        final HttpSession http;final String principal;final long created=System.currentTimeMillis();
        volatile boolean revoked;Session socket;
        Binding(HttpSession http,String principal){this.http=http;this.principal=principal;}
        boolean valid(){try{return !revoked && (http.getMaxInactiveInterval()<=0 || System.currentTimeMillis()-http.getLastAccessedTime()<http.getMaxInactiveInterval()*1000L);}catch(IllegalStateException expired){return false;}}
    }
    @PostConstruct void start(){timer=executor.scheduleAtFixedRate(this::expire,1,1,TimeUnit.SECONDS);}
    public boolean reserve(String id,HttpSession http,String principal){
        expire();return pending.size()<1000 && active.size()<1000 && pending.putIfAbsent(id,new Binding(http,principal))==null;
    }
    public void opened(String id,Session socket){
        Binding b=pending.remove(id);
        if(b==null || socket.getUserPrincipal()==null || !b.principal.equals(socket.getUserPrincipal().getName()) || !b.valid()){close(socket);return;}
        synchronized(b){b.socket=socket;if(!b.valid()){close(socket);return;}socket.getAsyncRemote().setSendTimeout(2000);active.put(socket.getId(),b);}
    }
    public void closed(Session socket){active.remove(socket.getId());}
    public void revoke(HttpSession http){
        pending.entrySet().removeIf(e->e.getValue().http==http);
        active.forEach((id,b)->{if(b.http==http)revoke(id,b);});
    }
    private void revoke(String id,Binding b){synchronized(b){b.revoked=true;active.remove(id,b);if(b.socket!=null)close(b.socket);}}
    private void close(Session socket){try{socket.close(new CloseReason(CloseReason.CloseCodes.VIOLATED_POLICY,"Session unavailable"));}catch(Exception ignored){}}
    private void expire(){
        pending.entrySet().removeIf(e->!e.getValue().valid() || System.currentTimeMillis()-e.getValue().created>30000);
        active.forEach((id,b)->{if(!b.valid())revoke(id,b);});
    }
    public void publish(String json){
        active.forEach((id,b)->{synchronized(b){
            if(!b.valid()){revoke(id,b);return;}
            try{b.socket.getAsyncRemote().sendText(json,result->{if(!result.isOK())revoke(id,b);});}catch(Exception disconnected){revoke(id,b);}
        }});
    }
    @PreDestroy void stop(){if(timer!=null)timer.cancel(false);active.forEach(this::revoke);pending.clear();}
}
