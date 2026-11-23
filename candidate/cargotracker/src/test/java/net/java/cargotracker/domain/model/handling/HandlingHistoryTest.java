package net.java.cargotracker.domain.model.handling;

import static org.junit.Assert.*;

import java.lang.reflect.Field;
import java.util.Arrays;
import java.util.Date;

import net.java.cargotracker.application.util.DateUtil;
import net.java.cargotracker.domain.model.cargo.Cargo;
import net.java.cargotracker.domain.model.cargo.RouteSpecification;
import net.java.cargotracker.domain.model.cargo.TrackingId;
import net.java.cargotracker.domain.model.location.SampleLocations;
import net.java.cargotracker.domain.model.voyage.Voyage;
import net.java.cargotracker.domain.model.voyage.VoyageNumber;

import org.junit.Test;

//TODO This set of tests is very trivial, consider removing them.
public class HandlingHistoryTest {

	Cargo cargo = new Cargo(new TrackingId("ABC"), new RouteSpecification(
			SampleLocations.SHANGHAI, SampleLocations.DALLAS,
			DateUtil.toDate("2009-04-01")));
	Voyage voyage = new Voyage.Builder(new VoyageNumber("X25"),
			SampleLocations.HONGKONG)
			.addMovement(SampleLocations.SHANGHAI, new Date(), new Date())
			.addMovement(SampleLocations.DALLAS, new Date(), new Date())
			.build();
	HandlingEvent event1 = new HandlingEvent(cargo,
			DateUtil.toDate("2009-03-05"), new Date(100),
			HandlingEvent.Type.LOAD, SampleLocations.SHANGHAI, voyage);
	HandlingEvent event1duplicate = new HandlingEvent(cargo,
			DateUtil.toDate("2009-03-05"), new Date(200),
			HandlingEvent.Type.LOAD, SampleLocations.SHANGHAI, voyage);
	HandlingEvent event2 = new HandlingEvent(cargo,
			DateUtil.toDate("2009-03-10"), new Date(150),
			HandlingEvent.Type.UNLOAD, SampleLocations.DALLAS, voyage);
	HandlingHistory handlingHistory = new HandlingHistory(Arrays.asList(event2,
			event1, event1duplicate));

	@Test
	public void testDistinctEventsByCompletionTime() {
		assertEquals(Arrays.asList(event1, event2),
				handlingHistory.getDistinctEventsByCompletionTime());
	}

	@Test
	public void testMostRecentlyCompletedEvent() {
		assertEquals(event2, handlingHistory.getMostRecentlyCompletedEvent());
	}

	@Test
	public void testDistinctEventsWithEqualCompletionTimesAreBothRetained() {
		Date completion = new Date(300);
		HandlingEvent unload = new HandlingEvent(cargo, completion,
				new Date(400), HandlingEvent.Type.UNLOAD,
				SampleLocations.DALLAS, voyage);
		HandlingEvent customs = new HandlingEvent(cargo, completion,
				new Date(500), HandlingEvent.Type.CUSTOMS,
				SampleLocations.DALLAS);

		HandlingHistory history = new HandlingHistory(Arrays.asList(unload,
				customs));

		assertEquals(2, history.getDistinctEventsByCompletionTime().size());
		assertTrue(history.getDistinctEventsByCompletionTime().contains(unload));
		assertTrue(history.getDistinctEventsByCompletionTime().contains(customs));
	}

	@Test
	public void testEqualCompletionTimesAreOrderedByRegistrationThenId() throws Exception {
		Date completion = new Date(300);
		HandlingEvent laterRegistration = new HandlingEvent(cargo, completion,
				DateUtil.toDate("2009-03-06"), HandlingEvent.Type.UNLOAD,
				SampleLocations.DALLAS, voyage);
		HandlingEvent sameDayHigherId = new HandlingEvent(cargo, completion,
				DateUtil.toDate("2009-03-05"), HandlingEvent.Type.CUSTOMS,
				SampleLocations.DALLAS);
		HandlingEvent sameDayLowerId = new HandlingEvent(cargo, completion,
				DateUtil.toDate("2009-03-05"), HandlingEvent.Type.CLAIM,
				SampleLocations.DALLAS);
		setId(sameDayHigherId, 20L);
		setId(sameDayLowerId, 10L);

		HandlingHistory history = new HandlingHistory(Arrays.asList(
				laterRegistration, sameDayHigherId, sameDayLowerId));

		assertEquals(Arrays.asList(sameDayLowerId, sameDayHigherId,
				laterRegistration), history.getDistinctEventsByCompletionTime());
	}

	private static void setId(HandlingEvent event, Long id) throws Exception {
		Field field = HandlingEvent.class.getDeclaredField("id");
		field.setAccessible(true);
		field.set(event, id);
	}
}
