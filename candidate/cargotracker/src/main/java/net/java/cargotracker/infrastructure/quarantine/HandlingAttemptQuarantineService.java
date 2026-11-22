package net.java.cargotracker.infrastructure.quarantine;

import jakarta.ejb.EJB;
import jakarta.ejb.EJBException;
import jakarta.ejb.Stateless;
import jakarta.annotation.security.RolesAllowed;
import jakarta.ejb.TransactionAttribute;
import jakarta.ejb.TransactionAttributeType;
import jakarta.json.Json;
import jakarta.json.JsonArrayBuilder;
import jakarta.json.JsonObjectBuilder;
import jakarta.annotation.Resource;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import javax.sql.DataSource;
import net.java.cargotracker.interfaces.handling.HandlingEventRegistrationAttempt;
import net.java.cargotracker.infrastructure.messaging.jms.HandlingEventRegistrationAttemptProducer;
import net.java.cargotracker.domain.model.cargo.TrackingId;
import net.java.cargotracker.domain.model.handling.HandlingEvent;
import net.java.cargotracker.domain.model.location.UnLocode;
import net.java.cargotracker.domain.model.voyage.VoyageNumber;

/** Persists expired handling attempts under a transactionally enforced logical payload cap. */
@Stateless
public class HandlingAttemptQuarantineService {
    @Resource(lookup = "java:jboss/datasources/CargoTrackerDS")
    private DataSource dataSource;
    @EJB
    private HandlingQuarantineCapacityAlert capacityAlert;
    @EJB
    private HandlingRequestIdempotencyService requestIds;
    @EJB
    private HandlingEventRegistrationAttemptProducer producer;

    @RolesAllowed("HandlingQuarantineWorker")
    @TransactionAttribute(TransactionAttributeType.REQUIRES_NEW)
    public void registerLegacyRequest(String requestId, HandlingEventRegistrationAttempt attempt) {
        requestIds.reserve(requestId, attempt);
    }

    @RolesAllowed("HandlingQuarantineWorker")
    @TransactionAttribute(TransactionAttributeType.REQUIRED)
    public void store(HandlingEventRegistrationAttempt attempt, String requestId, String messageKey) {
        if (!requestIds.eligibleForQuarantine(requestId, attempt)) {
            capacityAlert.pendingResolved(messageKey);
            return;
        }
        long payloadBytes = payloadSizeBytes(attempt);
        String payloadHash = HandlingRequestIdempotencyService.payloadHash(attempt);
        long capacity = HandlingQuarantineConfiguration.capacityBytes();
        try (Connection connection = dataSource.getConnection()) {
            lockState(connection);
            long used = storedPayloadBytes(connection);
            if (payloadBytes > capacity - used) {
                throw new QuarantineCapacityFullException(requestId, messageKey, used, payloadBytes, capacity);
            }
            String sql = "INSERT INTO cargo.handling_attempt_quarantine "
                    + "(tracking_id,event_type,unlocode,voyage_number,registration_time,completion_time,"
                    + "received_at,expires_at,payload_size_bytes,request_id,payload_sha256) "
                    + "VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP,"
                    + "CURRENT_TIMESTAMP + (? * INTERVAL '1 second'),?,?,?)";
            try (PreparedStatement statement = connection.prepareStatement(sql)) {
                statement.setString(1, attempt.getTrackingId().toString());
                statement.setString(2, attempt.getType().name());
                statement.setString(3, attempt.getUnLocode().getIdString());
                statement.setString(4, attempt.getVoyageNumber() == null
                        ? null : attempt.getVoyageNumber().toString());
                statement.setTimestamp(5, Timestamp.from(attempt.getRegistrationTime().toInstant()));
                statement.setTimestamp(6, Timestamp.from(attempt.getCompletionTime().toInstant()));
                statement.setLong(7, HandlingQuarantineConfiguration.retentionSeconds());
                statement.setLong(8, payloadBytes);
                statement.setString(9, requestId);
                statement.setString(10, payloadHash);
                statement.executeUpdate();
                requestIds.markQuarantined(requestId);
            }
            // Resolve only this broker message after its payload and identity are durable.
            capacityAlert.pendingResolved(messageKey);
        } catch (QuarantineCapacityFullException full) {
            throw full;
        } catch (SQLException | RuntimeException failure) {
            if (failure instanceof EJBException ejb) throw ejb;
            throw new EJBException("Handling quarantine persistence failed", failure);
        }
    }

    @RolesAllowed("HandlingQuarantineWorker")
    @TransactionAttribute(TransactionAttributeType.REQUIRED)
    public int purgeExpired() {
        try (Connection connection = dataSource.getConnection()) {
            lockState(connection);
            int removed;
            try (PreparedStatement statement = connection.prepareStatement(
                    "DELETE FROM cargo.handling_attempt_quarantine WHERE expires_at <= CURRENT_TIMESTAMP")) {
                removed = statement.executeUpdate();
            }

            return removed;
        } catch (SQLException | RuntimeException failure) {
            if (failure instanceof EJBException ejb) throw ejb;
            throw new EJBException("Handling quarantine retention cleanup failed", failure);
        }
    }

    @RolesAllowed("Administrator")
    @TransactionAttribute(TransactionAttributeType.REQUIRED)
    public jakarta.json.JsonObject snapshot() {
        long capacity = HandlingQuarantineConfiguration.capacityBytes();
        long used;
        JsonArrayBuilder entries = Json.createArrayBuilder();
        try (Connection connection = dataSource.getConnection()) {
            used = storedPayloadBytes(connection);
            String sql = "SELECT id,request_id,tracking_id,event_type,unlocode,voyage_number,completion_time,"
                    + "received_at,expires_at,last_replayed_at,last_replayed_by "
                    + "FROM cargo.handling_attempt_quarantine WHERE expires_at > CURRENT_TIMESTAMP ORDER BY received_at,id";
            try (PreparedStatement statement = connection.prepareStatement(sql);
                    ResultSet rows = statement.executeQuery()) {
                while (rows.next()) {
                    JsonObjectBuilder item = Json.createObjectBuilder()
                            .add("id", rows.getLong("id"))
                            .add("requestId", rows.getString("request_id") == null ? "legacy" : rows.getString("request_id"))
                            .add("trackingId", rows.getString("tracking_id"))
                            .add("eventType", rows.getString("event_type"))
                            .add("unLocode", rows.getString("unlocode"))
                            .add("completionTime", instant(rows.getTimestamp("completion_time")))
                            .add("receivedAt", instant(rows.getTimestamp("received_at")))
                            .add("expiresAt", instant(rows.getTimestamp("expires_at")));
                    nullable(item, "voyageNumber", rows.getString("voyage_number"));
                    nullable(item, "lastReplayedAt", instantOrNull(rows.getTimestamp("last_replayed_at")));
                    nullable(item, "lastReplayedBy", rows.getString("last_replayed_by"));
                    entries.add(item);
                }
            }
            return Json.createObjectBuilder()
                    .add("capacityBytes", capacity)
                    .add("storedPayloadBytes", used)
                    .add("retentionSeconds", HandlingQuarantineConfiguration.retentionSeconds())
                    .add("capacityAlertActive", capacityAlert.isActive())
                    .add("pendingIntakeCount", capacityAlert.pendingCount())
                    .add("entries", entries)
                    .build();
        } catch (SQLException | RuntimeException failure) {
            if (failure instanceof EJBException ejb) throw ejb;
            throw new EJBException("Handling quarantine snapshot failed", failure);
        }
    }



    @RolesAllowed("Administrator")
    @TransactionAttribute(TransactionAttributeType.REQUIRED)
    public jakarta.json.JsonObject replay(long id, String replayedBy) {
        try (Connection connection = dataSource.getConnection()) {
            HandlingEventRegistrationAttempt attempt;
            String requestId;
            try (PreparedStatement statement = connection.prepareStatement(
                    "SELECT request_id,tracking_id,event_type,unlocode,voyage_number,registration_time,completion_time,"
                    + "(expires_at > CURRENT_TIMESTAMP) AS retained "
                    + "FROM cargo.handling_attempt_quarantine WHERE id=?")) {
                statement.setLong(1, id);
                try (ResultSet row = statement.executeQuery()) {
                    if (!row.next()) {
                        if (hasReplayAudit(connection, id)) {
                            throw new HandlingReplayConflictException("Quarantine entry was already replayed");
                        }
                        throw new jakarta.ws.rs.NotFoundException("Quarantine entry not found");
                    }
                    if (!row.getBoolean("retained")) {
                        throw new HandlingReplayConflictException("Quarantine entry has expired");
                    }
                    requestId = row.getString("request_id");
                    attempt = new HandlingEventRegistrationAttempt(
                            row.getTimestamp("registration_time"), row.getTimestamp("completion_time"),
                            new TrackingId(row.getString("tracking_id")),
                            row.getString("voyage_number") == null ? null : new VoyageNumber(row.getString("voyage_number")),
                            HandlingEvent.Type.valueOf(row.getString("event_type")),
                            new UnLocode(row.getString("unlocode")));
                }
            }
            if (requestId == null) {
                requestId = "legacy-quarantine-" + id;
                requestIds.reserve(requestId, attempt);
                requestIds.markQuarantined(requestId);
                try (PreparedStatement update = connection.prepareStatement(
                        "UPDATE cargo.handling_attempt_quarantine SET request_id=?,payload_sha256=? WHERE id=?")) {
                    update.setString(1, requestId);
                    update.setString(2, HandlingRequestIdempotencyService.payloadHash(attempt));
                    update.setLong(3, id);
                    update.executeUpdate();
                }
            }
            requestIds.prepareReplay(requestId, attempt);
            producer.publishReplay(attempt, requestId);
            try (PreparedStatement audit = connection.prepareStatement(
                    "INSERT INTO cargo.handling_quarantine_replay_audit (quarantine_id,replayed_by,request_id) VALUES (?,?,?)")) {
                audit.setLong(1, id);
                audit.setString(2, replayedBy);
                audit.setString(3, requestId);
                audit.executeUpdate();
            }
            // The replay audit preserves the operator action. Removing this payload releases
            // its unique request ID so a later failed replay can be quarantined as a new entry.
            try (PreparedStatement delete = connection.prepareStatement(
                    "DELETE FROM cargo.handling_attempt_quarantine WHERE id=? AND expires_at > CURRENT_TIMESTAMP")) {
                delete.setLong(1, id);
                if (delete.executeUpdate() != 1) {
                    throw new HandlingReplayConflictException("Quarantine entry expired before replay completed");
                }
            }
            return Json.createObjectBuilder().add("id", id).add("requestId", requestId)
                    .add("status", "QUEUED").build();
        } catch (SQLException failure) {
            throw new EJBException("Handling quarantine replay could not be recorded", failure);
        }
    }

    private static boolean hasReplayAudit(Connection connection, long quarantineId) throws SQLException {
        try (PreparedStatement statement = connection.prepareStatement(
                "SELECT EXISTS (SELECT 1 FROM cargo.handling_quarantine_replay_audit WHERE quarantine_id=?)")) {
            statement.setLong(1, quarantineId);
            try (ResultSet row = statement.executeQuery()) {
                if (!row.next()) throw new SQLException("Replay audit existence query returned no row");
                return row.getBoolean(1);
            }
        }
    }
    static long payloadSizeBytes(HandlingEventRegistrationAttempt attempt) {
        String canonical = String.join("\n",
                attempt.getTrackingId().toString(), attempt.getType().name(),
                attempt.getUnLocode().getIdString(),
                attempt.getVoyageNumber() == null ? "" : attempt.getVoyageNumber().toString(),
                attempt.getRegistrationTime().toInstant().toString(),
                attempt.getCompletionTime().toInstant().toString());
        return canonical.getBytes(StandardCharsets.UTF_8).length;
    }

    private static void lockState(Connection connection) throws SQLException {
        try (PreparedStatement statement = connection.prepareStatement(
                "SELECT singleton_id FROM cargo.handling_quarantine_state WHERE singleton_id=1 FOR UPDATE");
                ResultSet row = statement.executeQuery()) {
            if (!row.next()) throw new SQLException("Quarantine state row is missing");
        }
    }

    private static long storedPayloadBytes(Connection connection) throws SQLException {
        try (PreparedStatement statement = connection.prepareStatement(
                "SELECT COALESCE(SUM(payload_size_bytes),0) FROM cargo.handling_attempt_quarantine "
                        + "WHERE expires_at > CURRENT_TIMESTAMP");
                ResultSet row = statement.executeQuery()) {
            if (!row.next()) throw new SQLException("Quarantine size query returned no row");
            return row.getLong(1);
        }
    }

    private static String instant(Timestamp timestamp) { return timestamp.toInstant().toString(); }
    private static String instantOrNull(Timestamp timestamp) { return timestamp == null ? null : instant(timestamp); }
    private static void nullable(JsonObjectBuilder builder, String name, String value) {
        if (value == null) builder.addNull(name);
        else builder.add(name, value);
    }
}
