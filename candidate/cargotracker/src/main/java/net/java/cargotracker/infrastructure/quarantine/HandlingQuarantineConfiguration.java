package net.java.cargotracker.infrastructure.quarantine;

/** Validated external configuration for bounded handling-event quarantine. */
public final class HandlingQuarantineConfiguration {
    public static final String CAPACITY_PROPERTY = "cargo.handling.quarantine.max.bytes";
    public static final String RETENTION_PROPERTY = "cargo.handling.quarantine.retention.seconds";
    public static final long DEFAULT_CAPACITY_BYTES = 1_073_741_824L;
    public static final long DEFAULT_RETENTION_SECONDS = 604_800L;

    private HandlingQuarantineConfiguration() { }

    public static long capacityBytes() {
        return capacityBytes(System.getProperty(CAPACITY_PROPERTY));
    }

    public static long retentionSeconds() {
        return retentionSeconds(System.getProperty(RETENTION_PROPERTY));
    }

    static long capacityBytes(String configured) {
        return configured == null ? DEFAULT_CAPACITY_BYTES
                : positiveLong(CAPACITY_PROPERTY, configured, Long.MAX_VALUE);
    }

    static long retentionSeconds(String configured) {
        return configured == null ? DEFAULT_RETENTION_SECONDS
                : positiveLong(RETENTION_PROPERTY, configured, DEFAULT_RETENTION_SECONDS);
    }

    private static long positiveLong(String property, String configured, long maximum) {
        try {
            long value = Long.parseLong(configured.trim());
            if (value <= 0 || value > maximum) throw new IllegalArgumentException();
            return value;
        } catch (IllegalArgumentException invalid) {
            throw new IllegalStateException("System property " + property
                    + " must be between 1 and " + maximum, invalid);
        }
    }
}
