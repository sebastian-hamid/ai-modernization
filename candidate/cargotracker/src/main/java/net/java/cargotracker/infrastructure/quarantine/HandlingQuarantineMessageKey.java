package net.java.cargotracker.infrastructure.quarantine;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import net.java.cargotracker.interfaces.handling.HandlingEventRegistrationAttempt;

/** Stable opaque identity for a broker message across expiry routing and redelivery. */
public final class HandlingQuarantineMessageKey {
    private HandlingQuarantineMessageKey() { }

    public static String from(String messageKey, String requestId, String jmsMessageId) {
        String stableValue = nonBlank(messageKey) ? messageKey
                : nonBlank(jmsMessageId) ? jmsMessageId : requestId;
        if (!nonBlank(stableValue)) throw new IllegalArgumentException("A stable handling message identity is required");
        return sha256(stableValue);
    }

    /** Compatibility identity for pre-request-ID messages; registration time distinguishes separate submissions. */
    public static String legacyRequestId(String jmsMessageId, HandlingEventRegistrationAttempt attempt) {
        String stableValue = nonBlank(jmsMessageId) ? jmsMessageId
                : attempt.getRegistrationTime().toInstant() + "\n" + HandlingRequestIdempotencyService.payloadHash(attempt);
        return "legacy-" + sha256(stableValue);
    }

    private static boolean nonBlank(String value) { return value != null && !value.isBlank(); }

    private static String sha256(String value) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                    .digest(value.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException impossible) {
            throw new IllegalStateException("SHA-256 is unavailable", impossible);
        }
    }
}
