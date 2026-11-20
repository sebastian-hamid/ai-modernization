package net.java.cargotracker.characterization;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import java.lang.reflect.Field;
import java.lang.reflect.Proxy;
import java.util.Date;
import java.util.List;
import net.java.cargotracker.application.RouteSelectionException;
import net.java.cargotracker.application.internal.DefaultBookingService;
import net.java.cargotracker.domain.model.cargo.Cargo;
import net.java.cargotracker.domain.model.cargo.CargoRepository;
import net.java.cargotracker.domain.model.cargo.Itinerary;
import net.java.cargotracker.domain.model.cargo.RoutingStatus;
import net.java.cargotracker.domain.model.cargo.RouteSpecification;
import net.java.cargotracker.domain.model.cargo.TrackingId;
import net.java.cargotracker.domain.model.location.LocationRepository;
import net.java.cargotracker.domain.model.location.SampleLocations;
import net.java.cargotracker.domain.model.location.UnLocode;
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

    @Test
    public void assigningUnsuitableRouteToKnownCargoIsRejectedBeforeStore() throws Exception {
        TrackingId trackingId = new TrackingId("KNOWN01");
        Cargo cargo = new Cargo(trackingId, new RouteSpecification(
                SampleLocations.SHANGHAI, SampleLocations.GOTHENBURG,
                new Date(Long.MAX_VALUE)));
        CargoRepository cargoRepository = proxy(CargoRepository.class,
                (method, args) -> {
                    if ("find".equals(method)) {
                        return trackingId.equals(args[0]) ? cargo : null;
                    }
                    if ("store".equals(method)) {
                        storeCalls++;
                        return null;
                    }
                    throw new UnsupportedOperationException(method);
                });
        inject("cargoRepository", cargoRepository);

        try {
            service.assignCargoToRoute(Itinerary.EMPTY_ITINERARY, trackingId);
        } catch (RouteSelectionException expected) {
            assertEquals(0, storeCalls);
            assertEquals(Itinerary.EMPTY_ITINERARY, cargo.getItinerary());
            assertEquals(RoutingStatus.NOT_ROUTED,
                    cargo.getDelivery().getRoutingStatus());
            return;
        }
        throw new AssertionError("A route that misses the cargo endpoints must be rejected");
    }

    @Test
    public void bookingWithUnknownOriginIsRejectedBeforeStore() throws Exception {
        assertUnknownLocationBookingRejected("QZABC", "FIHEL",
                "Origin is required");
    }

    @Test
    public void bookingWithUnknownDestinationIsRejectedBeforeStore() throws Exception {
        assertUnknownLocationBookingRejected("CNHKG", "QZABC",
                "Destination is required");
    }

    private void assertUnknownLocationBookingRejected(String origin,
            String destination, String expectedMessage) throws Exception {
        TrackingId generatedId = new TrackingId("BOOKING1");
        CargoRepository cargoRepository = proxy(CargoRepository.class,
                (method, args) -> {
                    if ("nextTrackingId".equals(method)) {
                        return generatedId;
                    }
                    if ("store".equals(method)) {
                        storeCalls++;
                        return null;
                    }
                    throw new UnsupportedOperationException(method);
                });
        LocationRepository locationRepository = proxy(LocationRepository.class,
                (method, args) -> {
                    if ("find".equals(method)) {
                        UnLocode code = (UnLocode) args[0];
                        if ("QZABC".equals(code.getIdString())) {
                            return null;
                        }
                        if ("CNHKG".equals(code.getIdString())) {
                            return SampleLocations.HONGKONG;
                        }
                        if ("FIHEL".equals(code.getIdString())) {
                            return SampleLocations.HELSINKI;
                        }
                    }
                    throw new UnsupportedOperationException(method);
                });
        inject("cargoRepository", cargoRepository);
        inject("locationRepository", locationRepository);

        try {
            service.bookNewCargo(new UnLocode(origin), new UnLocode(destination),
                    new Date(Long.MAX_VALUE));
            throw new AssertionError("Unknown endpoint must be rejected");
        } catch (NullPointerException expected) {
            assertEquals(expectedMessage, expected.getMessage());
            assertEquals(0, storeCalls);
        }
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
