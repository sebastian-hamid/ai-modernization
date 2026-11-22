-- Track each broker message blocked by quarantine capacity until its payload commits.
CREATE TABLE cargo.handling_quarantine_pending (
    message_key CHAR(64) PRIMARY KEY CHECK (message_key ~ '^[0-9a-f]{64}$'),
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
GRANT SELECT, INSERT, UPDATE, DELETE ON cargo.handling_quarantine_pending TO cargo_app;