package lab.fixture;

import jakarta.ejb.EJB;
import jakarta.ejb.EJBAccessException;
import jakarta.ejb.EJBException;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.inject.Inject;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import net.java.cargotracker.application.BookingService;
import net.java.cargotracker.domain.model.cargo.Cargo;
import net.java.cargotracker.domain.model.cargo.CargoRepository;
import net.java.cargotracker.domain.model.cargo.Itinerary;
import net.java.cargotracker.domain.model.cargo.TrackingId;
import net.java.cargotracker.domain.model.location.UnLocode;
import net.java.cargotracker.domain.service.RoutingService;

/** Test-only direct BookingService invoker, added only to disposable fixture images. */
public final class BookingApiProbe extends HttpServlet {
    @EJB private BookingService bookingService;
    @Inject private CargoRepository cargoRepository;
    @EJB private RoutingService routingService;
    private static final Map<String,Itinerary> PREPARED = new ConcurrentHashMap<>();

    @Override protected void doPost(HttpServletRequest request,HttpServletResponse response)throws IOException {
        String operation=request.getParameter("operation");
        String tracking=request.getParameter("trackingId");
        try {
            if("book".equals(operation)) {
                var deadline=new SimpleDateFormat("yyyy-MM-dd",Locale.ROOT).parse("2035-01-01");
                TrackingId created=bookingService.bookNewCargo(new UnLocode("FIHEL"),new UnLocode("CNSHA"),deadline);
                response.setStatus(201);response.setContentType("text/plain;charset=UTF-8");
                response.getWriter().write(created.getIdString());return;
            }
            if("prepare-route".equals(operation)) {
                Cargo cargo=cargoRepository.find(new TrackingId(tracking));
                if(cargo==null){response.sendError(404);return;}
                List<Itinerary> routes=routingService.fetchRoutesForSpecification(cargo.getRouteSpecification());
                if(routes.isEmpty()){response.sendError(422);return;}
                PREPARED.put(tracking,routes.get(0));response.setStatus(204);return;
            }
            if("assign".equals(operation)) {
                Itinerary route=PREPARED.get(tracking);
                if(route==null){response.sendError(409);return;}
                bookingService.assignCargoToRoute(route,new TrackingId(tracking));
                response.setStatus(204);return;
            }
            if("destination".equals(operation)) {
                bookingService.changeDestination(new TrackingId(tracking),new UnLocode("USNYC"));
                response.setStatus(204);return;
            }
            response.sendError(400);
        } catch(RuntimeException failure) {
            if(hasAccessDenial(failure)) {
                response.setHeader("X-Fixture-Probe-Result","booking-service-role-denied");
                response.setStatus(403);return;
            }
            response.setHeader("X-Fixture-Probe-Failure",failure.getClass().getSimpleName());
            response.sendError(500);
        } catch(Exception failure) {
            response.setHeader("X-Fixture-Probe-Failure",failure.getClass().getSimpleName());
            response.sendError(500);
        }
    }

    private static boolean hasAccessDenial(Throwable failure) {
        for(Throwable current=failure;current!=null;current=current.getCause()) {
            if(current instanceof EJBAccessException)return true;
            if(current.getCause()==current)return false;
        }
        return false;
    }
}
