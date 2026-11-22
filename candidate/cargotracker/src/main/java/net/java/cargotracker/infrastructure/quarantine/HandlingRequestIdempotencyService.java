package net.java.cargotracker.infrastructure.quarantine;

import jakarta.annotation.Resource;
import jakarta.ejb.EJBException;
import jakarta.ejb.Stateless;
import jakarta.ejb.TransactionAttribute;
import jakarta.ejb.TransactionAttributeType;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.HexFormat;
import net.java.cargotracker.interfaces.handling.HandlingEventRegistrationAttempt;
import javax.sql.DataSource;

/** Transactional request identity shared by producer, business consumer and quarantine worker. */
@Stateless
@jakarta.annotation.security.RolesAllowed({"Administrator", "Operator", "BatchWorker", "HandlingAttemptProducer", "HandlingWorker", "HandlingQuarantineWorker"})
public class HandlingRequestIdempotencyService {
    private static final String QUEUED = "QUEUED";
    private static final String QUARANTINED = "QUARANTINED";
    private static final String PROCESSED = "PROCESSED";
    @Resource(lookup = "java:jboss/datasources/CargoTrackerDS")
    private DataSource dataSource;

    /** Reserves a request ID before enqueue; the producer and JDBC write share the JTA transaction. */
    @TransactionAttribute(TransactionAttributeType.REQUIRED)
    public boolean reserve(String requestId, HandlingEventRegistrationAttempt attempt) {
        String hash = payloadHash(attempt);
        try (Connection connection = dataSource.getConnection();
                PreparedStatement insert = connection.prepareStatement(
                    "INSERT INTO cargo.handling_request_idempotency "
                    + "(request_id,payload_sha256,state) VALUES (?,?,?) "
                    + "ON CONFLICT (request_id) DO NOTHING RETURNING request_id")) {
            insert.setString(1, requestId);
            insert.setString(2, hash);
            insert.setString(3, QUEUED);
            try (ResultSet result = insert.executeQuery()) {
                if (result.next()) return true;
            }
            String existingHash = lockAndReadHash(connection, requestId);
            if (!MessageDigest.isEqual(existingHash.getBytes(StandardCharsets.US_ASCII),
                    hash.getBytes(StandardCharsets.US_ASCII))) {
                throw new HandlingRequestIdConflictException("Idempotency-Key was already used with a different payload");
            }
            return false;
        } catch (HandlingRequestIdConflictException conflict) {
            throw conflict;
        } catch (SQLException failure) {
            throw new EJBException("Could not reserve handling request identity", failure);
        }
    }

    /** Locks the identity until the business MDB transaction commits or rolls back. */
    @TransactionAttribute(TransactionAttributeType.REQUIRED)
    public boolean beginProcessing(String requestId, HandlingEventRegistrationAttempt attempt) {
        try (Connection connection = dataSource.getConnection()) {
            Identity identity = lock(connection, requestId);
            verifyHash(identity, attempt);
            if (PROCESSED.equals(identity.state())) return false;
            if (!QUEUED.equals(identity.state())) {
                throw new EJBException("Handling request is not eligible for business processing");
            }
            return true;
        } catch (SQLException failure) {
            throw new EJBException("Could not check handling request identity", failure);
        }
    }

    @TransactionAttribute(TransactionAttributeType.REQUIRED)
    public boolean eligibleForQuarantine(String requestId, HandlingEventRegistrationAttempt attempt) {
        try (Connection connection = dataSource.getConnection()) {
            Identity identity = lock(connection, requestId);
            verifyHash(identity, attempt);
            return QUEUED.equals(identity.state());
        } catch (SQLException failure) {
            throw new EJBException("Could not check expired handling request identity", failure);
        }
    }

    @TransactionAttribute(TransactionAttributeType.REQUIRED)
    public void markQuarantined(String requestId) {
        updateState(requestId, QUEUED, QUARANTINED, false);
    }

    @TransactionAttribute(TransactionAttributeType.REQUIRED)
    public void markProcessed(String requestId) {
        try (Connection connection = dataSource.getConnection();
                PreparedStatement statement = connection.prepareStatement(
                    "UPDATE cargo.handling_request_idempotency SET state=?,processed_at=CURRENT_TIMESTAMP "
                    + "WHERE request_id=? AND state=?")) {
            statement.setString(1, PROCESSED);
            statement.setString(2, requestId);
            statement.setString(3, QUEUED);
            if (statement.executeUpdate() != 1) throw new EJBException("Handling request identity changed during processing");
        } catch (SQLException failure) {
            throw new EJBException("Could not record handling request completion", failure);
        }
    }

    /** Moves only an actually quarantined request back to QUEUED for an explicit admin replay. */
    @TransactionAttribute(TransactionAttributeType.REQUIRED)
    public void prepareReplay(String requestId, HandlingEventRegistrationAttempt attempt) {
        try (Connection connection = dataSource.getConnection()) {
            Identity identity = lock(connection, requestId);
            verifyHash(identity, attempt);
            if (!QUARANTINED.equals(identity.state())) {
                throw new HandlingReplayConflictException("Handling request is not currently quarantined");
            }
            try (PreparedStatement statement = connection.prepareStatement(
                    "UPDATE cargo.handling_request_idempotency SET state=? WHERE request_id=? AND state=?")) {
                statement.setString(1, QUEUED);
                statement.setString(2, requestId);
                statement.setString(3, QUARANTINED);
                if (statement.executeUpdate() != 1) throw new EJBException("Handling request replay state changed");
            }
        } catch (SQLException failure) {
            throw new EJBException("Could not prepare handling request replay", failure);
        }
    }

    public static String payloadHash(HandlingEventRegistrationAttempt attempt) {
        String canonical = String.join("\n", attempt.getTrackingId().toString(), attempt.getType().name(),
                attempt.getUnLocode().getIdString(),
                attempt.getVoyageNumber() == null ? "" : attempt.getVoyageNumber().toString(),
                attempt.getCompletionTime().toInstant().toString());
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                    .digest(canonical.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException impossible) {
            throw new IllegalStateException("SHA-256 is unavailable", impossible);
        }
    }

    private void updateState(String requestId, String required, String next, boolean timestamp) {
        String sql = "UPDATE cargo.handling_request_idempotency SET state=?"
                + (timestamp ? ",processed_at=CURRENT_TIMESTAMP" : "") + " WHERE request_id=? AND state=?";
        try (Connection connection = dataSource.getConnection(); PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, next);
            statement.setString(2, requestId);
            statement.setString(3, required);
            if (statement.executeUpdate() != 1) throw new EJBException("Handling request identity state changed unexpectedly");
        } catch (SQLException failure) {
            throw new EJBException("Could not update handling request identity", failure);
        }
    }

    private static Identity lock(Connection connection, String requestId) throws SQLException {
        try (PreparedStatement statement = connection.prepareStatement(
                "SELECT payload_sha256,state FROM cargo.handling_request_idempotency WHERE request_id=? FOR UPDATE")) {
            statement.setString(1, requestId);
            try (ResultSet row = statement.executeQuery()) {
                if (!row.next()) throw new SQLException("Handling request identity is missing");
                return new Identity(row.getString(1).trim(), row.getString(2));
            }
        }
    }

    private static String lockAndReadHash(Connection connection, String requestId) throws SQLException {
        return lock(connection, requestId).hash();
    }

    private static void verifyHash(Identity identity, HandlingEventRegistrationAttempt attempt) {
        String hash = payloadHash(attempt);
        if (!MessageDigest.isEqual(identity.hash().getBytes(StandardCharsets.US_ASCII),
                hash.getBytes(StandardCharsets.US_ASCII))) {
            throw new HandlingRequestIdConflictException("Request ID does not match the stored handling payload");
        }
    }

    private record Identity(String hash, String state) { }
}
