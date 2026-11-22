package net.java.cargotracker.infrastructure.quarantine;

import org.junit.Test;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.fail;

public class HandlingQuarantineConfigurationCharacterizationTest {
    @Test public void defaultsMatchApprovedPolicy() {
        assertEquals(1_073_741_824L, HandlingQuarantineConfiguration.capacityBytes(null));
        assertEquals(604_800L, HandlingQuarantineConfiguration.retentionSeconds(null));
    }
    @Test public void acceptsPositiveOverridesWithinPolicy() {
        assertEquals(512L, HandlingQuarantineConfiguration.capacityBytes("512"));
        assertEquals(1L, HandlingQuarantineConfiguration.retentionSeconds("1"));
        assertEquals(604_800L, HandlingQuarantineConfiguration.retentionSeconds("604800"));
    }
    @Test public void rejectsMalformedOrNonPositiveCapacity() {
        assertIllegalState(() -> HandlingQuarantineConfiguration.capacityBytes(""));
        assertIllegalState(() -> HandlingQuarantineConfiguration.capacityBytes("  "));
        assertIllegalState(() -> HandlingQuarantineConfiguration.capacityBytes("nope"));
        assertIllegalState(() -> HandlingQuarantineConfiguration.capacityBytes("0"));
        assertIllegalState(() -> HandlingQuarantineConfiguration.capacityBytes("-1"));
        assertIllegalState(() -> HandlingQuarantineConfiguration.capacityBytes("9223372036854775808"));
    }
    @Test public void rejectsRetentionAboveSevenDays() {
        assertIllegalState(() -> HandlingQuarantineConfiguration.retentionSeconds("bad"));
        assertIllegalState(() -> HandlingQuarantineConfiguration.retentionSeconds("0"));
        assertIllegalState(() -> HandlingQuarantineConfiguration.retentionSeconds("-1"));
        assertIllegalState(() -> HandlingQuarantineConfiguration.retentionSeconds("604801"));
    }
    private static void assertIllegalState(Runnable action) {
        try { action.run(); fail("Expected configuration to be rejected"); }
        catch (IllegalStateException expected) { }
    }
}
