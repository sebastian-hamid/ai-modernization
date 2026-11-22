-- Bounded logical-payload quarantine for expired handling attempts.
-- Immutable after publication: future changes use a new V<n> migration.
CREATE TABLE cargo.handling_attempt_quarantine (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tracking_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(32) NOT NULL,
    unlocode VARCHAR(5) NOT NULL,
    voyage_number VARCHAR(255),
    registration_time TIMESTAMPTZ NOT NULL,
    completion_time TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    payload_size_bytes BIGINT NOT NULL CHECK (payload_size_bytes > 0),
    last_replayed_at TIMESTAMPTZ,
    last_replayed_by VARCHAR(255)
);
CREATE INDEX idx_handling_attempt_quarantine_expiry
    ON cargo.handling_attempt_quarantine (expires_at);
CREATE TABLE cargo.handling_quarantine_state (
    singleton_id SMALLINT PRIMARY KEY CHECK (singleton_id = 1),
    capacity_alert_active BOOLEAN NOT NULL DEFAULT FALSE,
    capacity_alert_started_at TIMESTAMPTZ,
    last_capacity_recovered_at TIMESTAMPTZ
);
INSERT INTO cargo.handling_quarantine_state (singleton_id) VALUES (1);
CREATE TABLE cargo.handling_quarantine_replay_audit (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    quarantine_id BIGINT NOT NULL REFERENCES cargo.handling_attempt_quarantine(id) ON DELETE CASCADE,
    replayed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    replayed_by VARCHAR(255) NOT NULL
);
CREATE INDEX idx_handling_quarantine_replay_audit_quarantine
    ON cargo.handling_quarantine_replay_audit (quarantine_id, replayed_at);
GRANT SELECT, INSERT, UPDATE, DELETE ON cargo.handling_attempt_quarantine,
    cargo.handling_quarantine_state, cargo.handling_quarantine_replay_audit TO cargo_app;
GRANT USAGE, SELECT ON SEQUENCE cargo.handling_attempt_quarantine_id_seq,
    cargo.handling_quarantine_replay_audit_id_seq TO cargo_app;
