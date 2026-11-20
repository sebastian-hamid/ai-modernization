package net.java.cargotracker.characterization;

import java.lang.reflect.Field;
import java.lang.reflect.Proxy;
import java.util.Collections;
import java.util.Date;
import java.util.concurrent.atomic.AtomicInteger;
import net.java.cargotracker.application.ApplicationEvents;
import net.java.cargotracker.application.internal.DefaultHandlingEventService;
import net.java.cargotracker.domain.model.cargo.Cargo;
import net.java.cargotracker.domain.model.cargo.RouteSpecification;
import net.java.cargotracker.domain.model.cargo.TrackingId;
import net.java.cargotracker.domain.model.handling.CannotCreateHandlingEventException;
import net.java.cargotracker.domain.model.handling.HandlingEvent;
import net.java.cargotracker.domain.model.handling.HandlingEventFactory;
import net.java.cargotracker.domain.model.handling.HandlingEventRepository;
import net.java.cargotracker.domain.model.handling.HandlingHistory;
import net.java.cargotracker.domain.model.location.SampleLocations;
import net.java.cargotracker.domain.model.location.UnLocode;
import net.java.cargotracker.domain.model.voyage.VoyageNumber;
import org.junit.Before;
import org.junit.Test;
import static org.junit.Assert.*;

public class HandlingEventServiceClaimTest {
    private final TrackingId trackingId = new TrackingId("CLAIM123");
    private final Cargo cargo = new Cargo(trackingId,
            new RouteSpecification(SampleLocations.HONGKONG,
                    SampleLocations.HELSINKI, new Date(1893456000000L)));
    private final HandlingEvent claim = new HandlingEvent(cargo,
            new Date(1893542400000L), new Date(1893542400000L),
            HandlingEvent.Type.CLAIM, SampleLocations.HELSINKI);
    private final AtomicInteger stored = new AtomicInteger();
    private final AtomicInteger handledEvents = new AtomicInteger();
    private final AtomicInteger factoryCalls = new AtomicInteger();
    private DefaultHandlingEventService service;

    @Before
    public void configure() throws Exception {
        service = new DefaultHandlingEventService();
        HandlingEventRepository repository = (HandlingEventRepository) Proxy
                .newProxyInstance(HandlingEventRepository.class.getClassLoader(),
                        new Class<?>[]{HandlingEventRepository.class},
                        (proxy, method, args) -> {
                            if ("lookupHandlingHistoryOfCargo".equals(method.getName())) {
                                assertEquals(trackingId, args[0]);
                                return new HandlingHistory(Collections.singletonList(claim));
                            }
                            if ("store".equals(method.getName())) {
                                stored.incrementAndGet();
                                return null;
                            }
                            throw new UnsupportedOperationException(method.getName());
                        });
        ApplicationEvents events = (ApplicationEvents) Proxy.newProxyInstance(
                ApplicationEvents.class.getClassLoader(),
                new Class<?>[]{ApplicationEvents.class},
                (proxy, method, args) -> {
                    if ("cargoWasHandled".equals(method.getName())) {
                        handledEvents.incrementAndGet();
                        return null;
                    }
                    throw new AssertionError("Unexpected event: " + method.getName());
                });
        HandlingEventFactory factory = new HandlingEventFactory() {
            @Override
            public HandlingEvent createHandlingEvent(Date registrationTime,
                    Date completionTime, TrackingId tracking, VoyageNumber voyage,
                    UnLocode location, HandlingEvent.Type type) {
                factoryCalls.incrementAndGet();
                return new HandlingEvent(cargo, completionTime, registrationTime,
                        type, SampleLocations.HELSINKI);
            }
        };
        inject("handlingEventRepository", repository);
        inject("applicationEvents", events);
        inject("handlingEventFactory", factory);
    }

    private void inject(String name, Object value) throws Exception {
        Field field = DefaultHandlingEventService.class.getDeclaredField(name);
        field.setAccessible(true);
        field.set(service, value);
    }

    @Test
    public void rejectsLoadAfterClaimBeforeFactoryStorageOrPublication() {
        try {
            service.registerHandlingEvent(new Date(1893628800000L), trackingId,
                    new VoyageNumber("0100S"), SampleLocations.HELSINKI.getUnLocode(),
                    HandlingEvent.Type.LOAD);
            fail("A LOAD after an existing CLAIM must be rejected");
        } catch (CannotCreateHandlingEventException expected) {
            assertEquals(0, factoryCalls.get());
            assertEquals(0, stored.get());
            assertEquals(0, handledEvents.get());
        }
    }

    @Test
    public void nonLoadEventRemainsAcceptedAfterClaim() throws Exception {
        service.registerHandlingEvent(new Date(1893628800000L), trackingId, null,
                SampleLocations.HELSINKI.getUnLocode(), HandlingEvent.Type.CUSTOMS);
        assertEquals(1, factoryCalls.get());
        assertEquals(1, stored.get());
        assertEquals(1, handledEvents.get());
    }
}
