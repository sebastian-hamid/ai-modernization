package net.java.cargotracker.characterization;

import java.lang.reflect.Field;
import java.lang.reflect.Proxy;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.util.Date;
import org.junit.Before;
import org.junit.Test;
import static org.junit.Assert.*;
import net.java.cargotracker.domain.model.cargo.*;
import net.java.cargotracker.domain.model.location.*;
import net.java.cargotracker.domain.model.voyage.*;
import net.java.cargotracker.domain.model.handling.*;

/** Exercises the real factory against deterministic repository lookups. */
public class HandlingFactoryCharacterizationTest {
    private final TrackingId tracking = new TrackingId("CHAR123");
    private final Voyage voyage = SampleVoyages.HONGKONG_TO_NEW_YORK;
    private HandlingEventFactory factory;

    @Before
    public void configureRepositories() throws Exception {
        Cargo cargo = new Cargo(tracking, new RouteSpecification(
                SampleLocations.HONGKONG, SampleLocations.HELSINKI,
                new Date(1483228800000L)));
        factory = new HandlingEventFactory();
        inject("cargoRepository", repository(CargoRepository.class, tracking, cargo));
        inject("locationRepository", repository(LocationRepository.class,
                SampleLocations.HONGKONG.getUnLocode(), SampleLocations.HONGKONG));
        inject("voyageRepository", repository(VoyageRepository.class,
                voyage.getVoyageNumber(), voyage));
    }

    private <T> T repository(Class<T> type, final Object key, final Object value) {
        return type.cast(Proxy.newProxyInstance(type.getClassLoader(),
                new Class<?>[]{type}, new InvocationHandler() {
                    @Override
                    public Object invoke(Object proxy, Method method, Object[] args) {
                        if ("find".equals(method.getName())) {
                            return key.equals(args[0]) ? value : null;
                        }
                        throw new UnsupportedOperationException(method.getName());
                    }
                }));
    }

    private void inject(String name, Object value) throws Exception {
        Field field = HandlingEventFactory.class.getDeclaredField(name);
        field.setAccessible(true);
        field.set(factory, value);
    }

    private HandlingEvent event(TrackingId id, VoyageNumber number,
            UnLocode location, HandlingEvent.Type type) throws Exception {
        return factory.createHandlingEvent(new Date(1483315200000L),
                new Date(1483228800000L), id, number, location, type);
    }

    private void invalidVoyageCombination(HandlingEvent.Type type,
            VoyageNumber number) throws Exception {
        try {
            event(tracking, number, SampleLocations.HONGKONG.getUnLocode(), type);
            fail("Expected rejection for " + type);
        } catch (CannotCreateHandlingEventException expected) {
            assertTrue(expected.getCause() instanceof IllegalArgumentException);
        }
    }

    @Test(expected = UnknownCargoException.class)
    public void rejectsUnknownCargo() throws Exception {
        event(new TrackingId("UNKNOWN"), null,
                SampleLocations.HONGKONG.getUnLocode(), HandlingEvent.Type.RECEIVE);
    }

    @Test(expected = UnknownLocationException.class)
    public void rejectsUnknownLocation() throws Exception {
        event(tracking, null, new UnLocode("ZZZZZ"), HandlingEvent.Type.RECEIVE);
    }

    @Test(expected = UnknownVoyageException.class)
    public void rejectsUnknownVoyage() throws Exception {
        event(tracking, new VoyageNumber("9999X"),
                SampleLocations.HONGKONG.getUnLocode(), HandlingEvent.Type.LOAD);
    }

    @Test public void loadRequiresVoyage() throws Exception {
        invalidVoyageCombination(HandlingEvent.Type.LOAD, null);
    }

    @Test public void unloadRequiresVoyage() throws Exception {
        invalidVoyageCombination(HandlingEvent.Type.UNLOAD, null);
    }

    @Test public void receiveProhibitsVoyage() throws Exception {
        invalidVoyageCombination(HandlingEvent.Type.RECEIVE, voyage.getVoyageNumber());
    }

    @Test public void claimProhibitsVoyage() throws Exception {
        invalidVoyageCombination(HandlingEvent.Type.CLAIM, voyage.getVoyageNumber());
    }

    @Test public void customsProhibitsVoyage() throws Exception {
        invalidVoyageCombination(HandlingEvent.Type.CUSTOMS, voyage.getVoyageNumber());
    }

    @Test public void acceptsReceiveWithoutVoyage() throws Exception {
        HandlingEvent event = event(tracking, null,
                SampleLocations.HONGKONG.getUnLocode(), HandlingEvent.Type.RECEIVE);
        assertEquals(HandlingEvent.Type.RECEIVE, event.getType());
        assertEquals(tracking, event.getCargo().getTrackingId());
        assertEquals(Voyage.NONE, event.getVoyage());
    }

    @Test public void acceptsLoadWithKnownVoyage() throws Exception {
        HandlingEvent event = event(tracking, voyage.getVoyageNumber(),
                SampleLocations.HONGKONG.getUnLocode(), HandlingEvent.Type.LOAD);
        assertEquals(HandlingEvent.Type.LOAD, event.getType());
        assertEquals(voyage, event.getVoyage());
        assertEquals(SampleLocations.HONGKONG, event.getLocation());
    }
}
