package net.java.cargotracker.characterization;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import java.lang.reflect.Field;
import java.lang.reflect.Proxy;
import java.util.List;
import net.java.cargotracker.application.RouteSelectionException;
import net.java.cargotracker.application.internal.DefaultBookingService;
import net.java.cargotracker.domain.model.cargo.Cargo;
import net.java.cargotracker.domain.model.cargo.CargoRepository;
import net.java.cargotracker.domain.model.cargo.Itinerary;
import net.java.cargotracker.domain.model.cargo.TrackingId;
import net.java.cargotracker.domain.service.RoutingService;
import org.junit.Before;
import org.junit.Test;

/** Covers stable negative booking-service contracts without a database. */
public class BookingServiceFailureCharacterizationTest {

    private DefaultBookingService service;
    private int storeCalls;

    @Before
    public void configureUnknownCargoRepositories() throws Exception {
        service = new DefaultBookingService();
        storeCalls = 0;
        CargoRepository cargoRepository = proxy(CargoRepository.class,
                (method, args) -> {
                    if ("find".equals(method)) {
                        return null;
                    }
                    if ("store".equals(method)) {
                        storeCalls++;
                        return null;
                    }
                    throw new UnsupportedOperationException(method);
                });
        RoutingService routingService = proxy(RoutingService.class,
                (method, args) -> {
                    if ("fetchRoutesForSpecification".equals(method)) {
                        throw new AssertionError("Routing must not run for unknown cargo");
                    }
                    throw new UnsupportedOperationException(method);
                });
        inject("cargoRepository", cargoRepository);
        inject("routingService", routingService);
    }

    @Test
    public void unknownCargoHasNoCandidateRoutes() {
        List<Itinerary> candidates = service.requestPossibleRoutesForCargo(
                new TrackingId("MISSING1"));

        assertTrue(candidates.isEmpty());
    }

    @Test
    public void assigningRouteToUnknownCargoIsRejectedBeforeStore() {
        try {
            service.assignCargoToRoute(new Itinerary(),
                    new TrackingId("MISSING2"));
        } catch (RouteSelectionException expected) {
            assertEquals(0, storeCalls);
            return;
        }
        throw new AssertionError("Unknown cargo route assignment must be rejected");
    }

    private void inject(String fieldName, Object value) throws Exception {
        Field field = DefaultBookingService.class.getDeclaredField(fieldName);
        field.setAccessible(true);
        field.set(service, value);
    }

    private static <T> T proxy(Class<T> type, RepositoryCall call) {
        return type.cast(Proxy.newProxyInstance(type.getClassLoader(),
                new Class<?>[]{type}, (proxy, method, args) ->
                        call.invoke(method.getName(), args)));
    }

    @FunctionalInterface
    private interface RepositoryCall {
        Object invoke(String method, Object[] args) throws Throwable;
    }
}
