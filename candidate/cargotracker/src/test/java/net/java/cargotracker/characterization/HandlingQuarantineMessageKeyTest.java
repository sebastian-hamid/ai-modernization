package net.java.cargotracker.characterization;

import java.util.Date;
import net.java.cargotracker.domain.model.cargo.TrackingId;
import net.java.cargotracker.domain.model.handling.HandlingEvent;
import net.java.cargotracker.domain.model.location.UnLocode;
import net.java.cargotracker.domain.model.voyage.VoyageNumber;
import net.java.cargotracker.infrastructure.quarantine.HandlingQuarantineMessageKey;
import net.java.cargotracker.interfaces.handling.HandlingEventRegistrationAttempt;
import org.junit.Test;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertTrue;

public class HandlingQuarantineMessageKeyTest {
    @Test
    public void legacyIdentityIsStableAcrossRedeliveryAndSeparatesDifferentSubmissions() {
        HandlingEventRegistrationAttempt firstDelivery = attempt(1_800_000_000_000L);
        HandlingEventRegistrationAttempt redelivery = attempt(1_800_000_000_000L);
        HandlingEventRegistrationAttempt secondSubmission = attempt(1_800_000_001_000L);

        String requestId = HandlingQuarantineMessageKey.legacyRequestId(null, firstDelivery);
        assertEquals(requestId, HandlingQuarantineMessageKey.legacyRequestId(null, redelivery));
        assertNotEquals(requestId, HandlingQuarantineMessageKey.legacyRequestId(null, secondSubmission));
        assertEquals(64, HandlingQuarantineMessageKey.from(null, requestId, null).length());
    }

    @Test
    public void messageKeyUsesStableProducerPropertyThenBrokerIdThenRequestId() {
        String producer = HandlingQuarantineMessageKey.from("producer-key", "request", "broker-id");
        assertEquals(producer, HandlingQuarantineMessageKey.from("producer-key", "other", "other-broker-id"));
        String broker = HandlingQuarantineMessageKey.from(null, "request", "broker-id");
        assertNotEquals(producer, broker);
        assertNotEquals(broker, HandlingQuarantineMessageKey.from(null, "request", "different-broker-id"));
        assertTrue(HandlingQuarantineMessageKey.from(null, "request", null)
                .equals(HandlingQuarantineMessageKey.from(null, "request", null)));
    }

    private static HandlingEventRegistrationAttempt attempt(long registrationTime) {
        return new HandlingEventRegistrationAttempt(new Date(registrationTime), new Date(1_893_456_000_000L),
                new TrackingId("ABC123"), new VoyageNumber("V001"), HandlingEvent.Type.LOAD,
                new UnLocode("FIHEL"));
    }
}
