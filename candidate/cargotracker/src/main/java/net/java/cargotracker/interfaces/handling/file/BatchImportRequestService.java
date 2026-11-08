package net.java.cargotracker.interfaces.handling.file;

import jakarta.annotation.Resource;
import jakarta.annotation.security.RolesAllowed;
import jakarta.annotation.security.RunAs;
import jakarta.ejb.EJB;
import jakarta.ejb.Lock;
import jakarta.ejb.LockType;
import jakarta.ejb.Singleton;
import jakarta.ejb.Startup;
import jakarta.ejb.ConcurrencyManagement;
import jakarta.ejb.ConcurrencyManagementType;
import jakarta.ejb.SessionContext;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/** Server-side admission control for the one supported Administrator import action. */
@Singleton
@Startup
@ConcurrencyManagement(ConcurrencyManagementType.CONTAINER)
@RunAs("BatchTrigger")
public class BatchImportRequestService {
    private static final long NONCE_TTL_SECONDS = 600;
    private static final int MAX_NONCES = 4096;
    private final Map<String, Long> issuedNonces = new ConcurrentHashMap<>();

    @EJB
    private BatchImportLauncher launcher;

    @RolesAllowed("Administrator")
    public String issueNonce(String sessionId, String nonce) {
        if (sessionId == null || nonce == null || !nonce.matches("[0-9a-f-]{36}")) {
            throw new IllegalArgumentException("Invalid import request context");
        }
        long now = Instant.now().getEpochSecond();
        issuedNonces.entrySet().removeIf(entry -> entry.getValue() <= now);
        if (issuedNonces.size() >= MAX_NONCES) {
            throw new IllegalStateException("Import request capacity is temporarily unavailable");
        }
        String key = key(sessionId, nonce);
        issuedNonces.put(key, now + NONCE_TTL_SECONDS);
        return nonce;
    }

    @RolesAllowed("Administrator")
    @Lock(LockType.WRITE)
    public BatchImportResult start(String sessionId, String nonce, String initiator) {
        if (!Boolean.getBoolean(BatchImportPaths.ENABLED_PROPERTY)) {
            throw new IllegalStateException("Import is disabled by server configuration");
        }
        String requestKey = key(sessionId, nonce);
        Long expiry = issuedNonces.remove(requestKey);
        long now = Instant.now().getEpochSecond();
        if (expiry == null || expiry <= now) {
            throw new IllegalStateException("Import request has expired or was already used");
        }
        if (initiator == null || initiator.isBlank()) {
            throw new SecurityException("Authenticated initiator is required");
        }
        String runId = UUID.randomUUID().toString();
        long executionId = launcher.start(runId, initiator);
        return new BatchImportResult(runId, executionId, initiator);
    }

    private static String key(String sessionId, String nonce) {
        return sessionId + ":" + nonce;
    }
}
