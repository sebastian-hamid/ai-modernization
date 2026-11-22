package net.java.cargotracker.characterization;

import net.java.cargotracker.infrastructure.messaging.jms.HandlingAttemptConfiguration;
import org.junit.After;
import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertThrows;

public class HandlingAttemptConfigurationCharacterizationTest {
    private final String original = System.getProperty(HandlingAttemptConfiguration.TTL_PROPERTY);

    @After
    public void restoreProperty() {
        if (original == null) {
            System.clearProperty(HandlingAttemptConfiguration.TTL_PROPERTY);
        } else {
            System.setProperty(HandlingAttemptConfiguration.TTL_PROPERTY, original);
        }
    }

    @Test
    public void defaultsToThirtySecondsWhenPropertyIsAbsent() {
        System.clearProperty(HandlingAttemptConfiguration.TTL_PROPERTY);
        assertEquals(30_000L, HandlingAttemptConfiguration.timeToLiveMillis());
    }

    @Test
    public void acceptsPositiveMillisecondOverride() {
        System.setProperty(HandlingAttemptConfiguration.TTL_PROPERTY, "1250");
        assertEquals(1_250L, HandlingAttemptConfiguration.timeToLiveMillis());
    }

    @Test
    public void rejectsMalformedAndNonpositiveOverrides() {
        for (String invalid : new String[] {"", "abc", "0", "-1"}) {
            System.setProperty(HandlingAttemptConfiguration.TTL_PROPERTY, invalid);
            assertThrows(IllegalStateException.class, HandlingAttemptConfiguration::timeToLiveMillis);
        }
    }
}
