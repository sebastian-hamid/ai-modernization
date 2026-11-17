package net.java.cargotracker.characterization;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.fail;
import java.util.Date;
import net.java.cargotracker.domain.model.cargo.RouteSpecification;
import net.java.cargotracker.domain.model.cargo.TrackingId;
import net.java.cargotracker.domain.model.location.SampleLocations;
import net.java.cargotracker.domain.model.location.UnLocode;
import org.junit.Test;

/** Characterizes the legacy domain input contract without changing behavior. */
public class DomainInputValidationCharacterizationTest {

    @Test
    public void normalizesValidUnLocodeToUppercase() {
        assertEquals("GBFXT", new UnLocode("gbfxt").getIdString());
    }

    @Test
    public void acceptsDigitsTwoThroughNineInLocationPart() {
        assertEquals("GBF2X", new UnLocode("gbf2x").getIdString());
        assertEquals("GBF9X", new UnLocode("gbf9x").getIdString());
    }

    @Test
    public void rejectsNullUnLocode() {
        try {
            new UnLocode(null);
            fail("Null UN/LOCODE must be rejected");
        } catch (NullPointerException expected) {
            // Current constructor contract.
        }
    }

    @Test(expected = NullPointerException.class)
    public void rejectsNullTrackingId() {
        new TrackingId(null);
    }

    @Test(expected = NullPointerException.class)
    public void rejectsNullRouteOrigin() {
        new RouteSpecification(null, SampleLocations.STOCKHOLM, new Date());
    }

    @Test(expected = NullPointerException.class)
    public void rejectsNullRouteDestination() {
        new RouteSpecification(SampleLocations.SHANGHAI, null, new Date());
    }

    @Test(expected = NullPointerException.class)
    public void rejectsNullArrivalDeadline() {
        new RouteSpecification(SampleLocations.SHANGHAI,
                SampleLocations.STOCKHOLM, null);
    }

    @Test(expected = IllegalArgumentException.class)
    public void rejectsIdenticalRouteOriginAndDestination() {
        new RouteSpecification(SampleLocations.SHANGHAI,
                SampleLocations.SHANGHAI, new Date());
    }

    @Test
    public void rejectsMalformedUnLocodeInputs() {
        String[] invalid = {"", "GBFX", "GBFXTT", "1BFXX", "GBF0X",
            "GBF1X", "GB FX", "GBF-X"};
        for (String input : invalid) {
            try {
                new UnLocode(input);
                fail("Malformed UN/LOCODE must be rejected: " + input);
            } catch (IllegalArgumentException expected) {
                // Current constructor contract.
            }
        }
    }
}
