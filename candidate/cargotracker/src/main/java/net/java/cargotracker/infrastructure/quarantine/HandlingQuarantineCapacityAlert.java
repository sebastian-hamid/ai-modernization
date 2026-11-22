package net.java.cargotracker.infrastructure.quarantine;

import jakarta.annotation.Resource;
import jakarta.ejb.Asynchronous;
import jakarta.ejb.EJBException;
import jakarta.ejb.Stateless;
import jakarta.ejb.TransactionAttribute;
import jakarta.ejb.TransactionAttributeType;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.logging.Logger;
import javax.sql.DataSource;

/** Persists operator alert state until every blocked intake message transfers. */
@Stateless
@jakarta.annotation.security.RolesAllowed({"Administrator", "HandlingQuarantineWorker"})
public class HandlingQuarantineCapacityAlert {
    private static final Logger LOG = Logger.getLogger(HandlingQuarantineCapacityAlert.class.getName());
    @Resource(lookup = "java:jboss/datasources/CargoTrackerDS")
    private DataSource dataSource;

    /** Runs after MDB rollback so pending state persists independently of the failed message transaction. */
    @Asynchronous
    @TransactionAttribute(TransactionAttributeType.REQUIRES_NEW)
    public void full(String requestId, String messageKey, long usedBytes, long messageBytes, long capacityBytes) {
        try (Connection connection = dataSource.getConnection()) {
            // Use the same lock order as the transfer service (request identity, then capacity state).
            // A delayed callback must not recreate a marker after this request has committed.
            if (!isQueued(connection, requestId)) return;
            lockState(connection);
            try (PreparedStatement pending = connection.prepareStatement(
                    "INSERT INTO cargo.handling_quarantine_pending "
                    + "(message_key,first_seen_at,last_seen_at) VALUES (?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP) "
                    + "ON CONFLICT (message_key) DO UPDATE SET last_seen_at=CURRENT_TIMESTAMP")) {
                pending.setString(1, messageKey);
                pending.executeUpdate();
            }
            boolean activated;
            try (PreparedStatement alert = connection.prepareStatement(
                    "UPDATE cargo.handling_quarantine_state "
                    + "SET capacity_alert_active=TRUE, "
                    + "capacity_alert_started_at=COALESCE(capacity_alert_started_at,CURRENT_TIMESTAMP) "
                    + "WHERE singleton_id=1 AND capacity_alert_active=FALSE")) {
                activated = alert.executeUpdate() > 0;
            }
            if (activated) {
                LOG.severe("HANDLING_QUARANTINE_FULL usedPayloadBytes=" + usedBytes
                        + " pendingPayloadBytes=" + messageBytes
                        + " configuredCapacityBytes=" + capacityBytes
                        + "; pendingMessages=" + pendingCount(connection)
                        + "; expired handling attempts remain pending in the durable intake queue");
            }
        } catch (SQLException failure) {
            throw new EJBException("Could not persist quarantine capacity alert", failure);
        }
    }

    /** Resolves only the message whose insertion committed; other blocked items keep the alert active. */
    @TransactionAttribute(TransactionAttributeType.REQUIRED)
    public boolean pendingResolved(String messageKey) {
        try (Connection connection = dataSource.getConnection()) {
            lockState(connection);
            try (PreparedStatement delete = connection.prepareStatement(
                    "DELETE FROM cargo.handling_quarantine_pending WHERE message_key=?")) {
                delete.setString(1, messageKey);
                delete.executeUpdate();
            }
            if (pendingCount(connection) != 0) return false;
            try (PreparedStatement alert = connection.prepareStatement(
                    "UPDATE cargo.handling_quarantine_state "
                    + "SET capacity_alert_active=FALSE, capacity_alert_started_at=NULL, "
                    + "last_capacity_recovered_at=CURRENT_TIMESTAMP "
                    + "WHERE singleton_id=1 AND capacity_alert_active=TRUE")) {
                boolean changed = alert.executeUpdate() > 0;
                if (changed) LOG.info("HANDLING_QUARANTINE_CAPACITY_RECOVERED; all blocked intake messages transferred");
                return changed;
            }
        } catch (SQLException failure) {
            throw new EJBException("Could not reconcile quarantine capacity alert", failure);
        }
    }

    @TransactionAttribute(TransactionAttributeType.REQUIRED)
    public long pendingCount() {
        try (Connection connection = dataSource.getConnection()) {
            return pendingCount(connection);
        } catch (SQLException failure) {
            throw new EJBException("Could not count blocked quarantine intake messages", failure);
        }
    }

    @TransactionAttribute(TransactionAttributeType.REQUIRED)
    public boolean isActive() {
        try (Connection connection = dataSource.getConnection();
                PreparedStatement statement = connection.prepareStatement(
                    "SELECT capacity_alert_active FROM cargo.handling_quarantine_state WHERE singleton_id=1");
                ResultSet row = statement.executeQuery()) {
            if (!row.next()) throw new SQLException("Quarantine state row is missing");
            return row.getBoolean(1);
        } catch (SQLException failure) {
            throw new EJBException("Could not read quarantine alert state", failure);
        }
    }

    private static boolean isQueued(Connection connection, String requestId) throws SQLException {
        try (PreparedStatement statement = connection.prepareStatement(
                "SELECT state='QUEUED' FROM cargo.handling_request_idempotency WHERE request_id=? FOR UPDATE")) {
            statement.setString(1, requestId);
            try (ResultSet row = statement.executeQuery()) { return row.next() && row.getBoolean(1); }
        }
    }

    private static long pendingCount(Connection connection) throws SQLException {
        try (PreparedStatement statement = connection.prepareStatement(
                "SELECT count(*) FROM cargo.handling_quarantine_pending");
                ResultSet row = statement.executeQuery()) {
            if (!row.next()) throw new SQLException("Pending quarantine count query returned no row");
            return row.getLong(1);
        }
    }

    private static void lockState(Connection connection) throws SQLException {
        try (PreparedStatement statement = connection.prepareStatement(
                "SELECT singleton_id FROM cargo.handling_quarantine_state WHERE singleton_id=1 FOR UPDATE");
                ResultSet row = statement.executeQuery()) {
            if (!row.next()) throw new SQLException("Quarantine state row is missing");
        }
    }
}