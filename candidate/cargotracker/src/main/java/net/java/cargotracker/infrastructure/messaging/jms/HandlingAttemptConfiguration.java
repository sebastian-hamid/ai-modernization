package net.java.cargotracker.infrastructure.messaging.jms;

/** Reads the externally supplied handling-attempt producer lifetime. */
public final class HandlingAttemptConfiguration {
    public static final String TTL_PROPERTY = "cargo.handling.attempt.ttl.ms";
    public static final long DEFAULT_TTL_MILLIS = 30_000L;

    private HandlingAttemptConfiguration() {
    }

    public static long timeToLiveMillis() {
        String configured = System.getProperty(TTL_PROPERTY);
        if (configured == null) {
            return DEFAULT_TTL_MILLIS;
        }
        try {
            long value = Long.parseLong(configured.trim());
            if (value <= 0) {
                throw new IllegalArgumentException();
            }
            return value;
        } catch (IllegalArgumentException invalid) {
            throw new IllegalStateException(
                    "System property " + TTL_PROPERTY + " must be a positive integer", invalid);
        }
    }
}
