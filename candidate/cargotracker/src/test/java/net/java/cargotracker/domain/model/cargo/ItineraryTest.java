package net.java.cargotracker.domain.model.cargo;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Date;
import java.util.List;
import net.java.cargotracker.domain.model.handling.HandlingEvent;
import net.java.cargotracker.domain.model.handling.HandlingHistory;
import net.java.cargotracker.domain.model.location.Location;
import net.java.cargotracker.domain.model.location.SampleLocations;
import net.java.cargotracker.domain.model.voyage.Voyage;
import net.java.cargotracker.domain.model.voyage.VoyageNumber;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;
import org.junit.Test;

public class ItineraryTest {

    private Voyage voyage = new Voyage.Builder(new VoyageNumber("0123"),
            SampleLocations.SHANGHAI)
            .addMovement(SampleLocations.ROTTERDAM, new Date(), new Date())
            .addMovement(SampleLocations.GOTHENBURG, new Date(), new Date())
            .build();
    private Voyage wrongVoyage = new Voyage.Builder(new VoyageNumber("666"),
            SampleLocations.NEWYORK)
            .addMovement(SampleLocations.STOCKHOLM, new Date(), new Date())
            .addMovement(SampleLocations.HELSINKI, new Date(), new Date())
            .build();

    @Test
    public void testCargoOnTrack() {
        TrackingId trackingId = new TrackingId("CARGO1");
        RouteSpecification routeSpecification = new RouteSpecification(
                SampleLocations.SHANGHAI, SampleLocations.GOTHENBURG,
                new Date());
        Cargo cargo = new Cargo(trackingId, routeSpecification);

        Itinerary itinerary = new Itinerary(Arrays.asList(new Leg(voyage,
                SampleLocations.SHANGHAI, SampleLocations.ROTTERDAM,
                new Date(), new Date()), new Leg(voyage,
                        SampleLocations.ROTTERDAM, SampleLocations.GOTHENBURG,
                        new Date(), new Date())));

        // Happy path
        HandlingEvent event = new HandlingEvent(cargo, new Date(), new Date(),
                HandlingEvent.Type.RECEIVE, SampleLocations.SHANGHAI);
        assertTrue(itinerary.isExpected(event));

        event = new HandlingEvent(cargo, new Date(), new Date(),
                HandlingEvent.Type.LOAD, SampleLocations.SHANGHAI, voyage);
        assertTrue(itinerary.isExpected(event));

        event = new HandlingEvent(cargo, new Date(), new Date(),
                HandlingEvent.Type.UNLOAD, SampleLocations.ROTTERDAM, voyage);
        assertTrue(itinerary.isExpected(event));

        event = new HandlingEvent(cargo, new Date(), new Date(),
                HandlingEvent.Type.LOAD, SampleLocations.ROTTERDAM, voyage);
        assertTrue(itinerary.isExpected(event));

        event = new HandlingEvent(cargo, new Date(), new Date(),
                HandlingEvent.Type.UNLOAD, SampleLocations.GOTHENBURG, voyage);
        assertTrue(itinerary.isExpected(event));

        event = new HandlingEvent(cargo, new Date(), new Date(),
                HandlingEvent.Type.CLAIM, SampleLocations.GOTHENBURG);
        assertTrue(itinerary.isExpected(event));

        // Customs event changes nothing
        event = new HandlingEvent(cargo, new Date(), new Date(),
                HandlingEvent.Type.CUSTOMS, SampleLocations.GOTHENBURG);
        assertTrue(itinerary.isExpected(event));

        // Received at the wrong location
        event = new HandlingEvent(cargo, new Date(), new Date(),
                HandlingEvent.Type.RECEIVE, SampleLocations.HANGZOU);
        assertFalse(itinerary.isExpected(event));

        // Loaded to onto the wrong ship, correct location
        event = new HandlingEvent(cargo, new Date(), new Date(),
                HandlingEvent.Type.LOAD, SampleLocations.ROTTERDAM, wrongVoyage);
        assertFalse(itinerary.isExpected(event));

        // Unloaded from the wrong ship in the wrong location
        event = new HandlingEvent(cargo, new Date(), new Date(),
                HandlingEvent.Type.UNLOAD, SampleLocations.HELSINKI,
                wrongVoyage);
        assertFalse(itinerary.isExpected(event));

        event = new HandlingEvent(cargo, new Date(), new Date(),
                HandlingEvent.Type.CLAIM, SampleLocations.ROTTERDAM);
        assertFalse(itinerary.isExpected(event));
    }

    @Test
    public void testNextExpectedEvent() {
        RouteSpecification routeSpecification = new RouteSpecification(
                SampleLocations.SHANGHAI, SampleLocations.GOTHENBURG,
                new Date(Long.MAX_VALUE));
        Cargo cargo = new Cargo(new TrackingId("CARGO1"), routeSpecification);
        Itinerary itinerary = new Itinerary(Arrays.asList(new Leg(voyage,
                SampleLocations.SHANGHAI, SampleLocations.ROTTERDAM,
                new Date(), new Date()), new Leg(voyage,
                SampleLocations.ROTTERDAM, SampleLocations.GOTHENBURG,
                new Date(), new Date())));
        cargo.assignToRoute(itinerary);

        assertNextActivity(cargo, HandlingEvent.Type.RECEIVE,
                SampleLocations.SHANGHAI, null);

        deriveProgress(cargo, event(cargo, HandlingEvent.Type.RECEIVE,
                SampleLocations.SHANGHAI, null));
        assertNextActivity(cargo, HandlingEvent.Type.LOAD,
                SampleLocations.SHANGHAI, voyage);

        deriveProgress(cargo, event(cargo, HandlingEvent.Type.LOAD,
                SampleLocations.SHANGHAI, voyage));
        assertNextActivity(cargo, HandlingEvent.Type.UNLOAD,
                SampleLocations.ROTTERDAM, voyage);

        deriveProgress(cargo, event(cargo, HandlingEvent.Type.UNLOAD,
                SampleLocations.ROTTERDAM, voyage));
        assertNextActivity(cargo, HandlingEvent.Type.LOAD,
                SampleLocations.ROTTERDAM, voyage);

        deriveProgress(cargo, event(cargo, HandlingEvent.Type.LOAD,
                SampleLocations.ROTTERDAM, voyage));
        assertNextActivity(cargo, HandlingEvent.Type.UNLOAD,
                SampleLocations.GOTHENBURG, voyage);

        deriveProgress(cargo, event(cargo, HandlingEvent.Type.UNLOAD,
                SampleLocations.GOTHENBURG, voyage));
        assertNextActivity(cargo, HandlingEvent.Type.CLAIM,
                SampleLocations.GOTHENBURG, null);

        deriveProgress(cargo, event(cargo, HandlingEvent.Type.CLAIM,
                SampleLocations.GOTHENBURG, null));
        assertTrue(cargo.getDelivery().getNextExpectedActivity().isEmpty());

        RouteSpecification incompatibleSpecification = new RouteSpecification(
                SampleLocations.NEWYORK, SampleLocations.GOTHENBURG,
                new Date(Long.MAX_VALUE));
        Cargo misroutedCargo = new Cargo(new TrackingId("CARGO2"),
                incompatibleSpecification);
        misroutedCargo.assignToRoute(itinerary);
        assertTrue(misroutedCargo.getDelivery().getNextExpectedActivity()
                .isEmpty());

        deriveProgress(misroutedCargo, event(misroutedCargo,
                HandlingEvent.Type.RECEIVE, SampleLocations.HANGZOU, null));
        assertTrue(misroutedCargo.getDelivery().isMisdirected());
        assertTrue(misroutedCargo.getDelivery().getNextExpectedActivity()
                .isEmpty());
    }

    private HandlingEvent event(Cargo cargo, HandlingEvent.Type type,
            Location location, Voyage eventVoyage) {
        if (eventVoyage == null) {
            return new HandlingEvent(cargo, new Date(), new Date(), type,
                    location);
        }
        return new HandlingEvent(cargo, new Date(), new Date(), type,
                location, eventVoyage);
    }

    private void deriveProgress(Cargo cargo, HandlingEvent event) {
        cargo.deriveDeliveryProgress(new HandlingHistory(Arrays.asList(event)));
    }

    private void assertNextActivity(Cargo cargo, HandlingEvent.Type type,
            Location location, Voyage expectedVoyage) {
        HandlingActivity actual = cargo.getDelivery().getNextExpectedActivity();
        assertEquals(type, actual.getType());
        assertEquals(location, actual.getLocation());
        assertEquals(expectedVoyage, actual.getVoyage());
    }

    @Test
    public void testCreateItinerary() {
        try {
            @SuppressWarnings("unused")
            Itinerary itinerary = new Itinerary(new ArrayList<Leg>());
            fail("An empty itinerary is not OK");
        } catch (IllegalArgumentException iae) {
            // Expected
        }

        try {
            List<Leg> legs = null;
            @SuppressWarnings("unused")
            Itinerary itinerary = new Itinerary(legs);
            fail("Null itinerary is not OK");
        } catch (NullPointerException npe) {
            // Expected
        }
    }
}
