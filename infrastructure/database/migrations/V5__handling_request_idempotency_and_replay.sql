-- Stable request identity and replay audit survive quarantine-entry retention.
ALTER TABLE cargo.handling_attempt_quarantine
    ADD COLUMN request_id VARCHAR(128),
    ADD COLUMN payload_sha256 CHAR(64);
CREATE UNIQUE INDEX uq_handling_quarantine_request_id
    ON cargo.handling_attempt_quarantine (request_id) WHERE request_id IS NOT NULL;

CREATE TABLE cargo.handling_request_idempotency (
    request_id VARCHAR(128) PRIMARY KEY
        CHECK (request_id ~ '^[A-Za-z0-9._:-]{1,128}$'),
    payload_sha256 CHAR(64) NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    state VARCHAR(16) NOT NULL CHECK (state IN ('QUEUED','QUARANTINED','PROCESSED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMPTZ
);

-- Replay audit is retained after the corresponding quarantine payload expires.
ALTER TABLE cargo.handling_quarantine_replay_audit
    DROP CONSTRAINT handling_quarantine_replay_audit_quarantine_id_fkey;
ALTER TABLE cargo.handling_quarantine_replay_audit
    ADD COLUMN request_id VARCHAR(128);
UPDATE cargo.handling_quarantine_replay_audit a
SET request_id = COALESCE(q.request_id, 'legacy-quarantine-' || a.quarantine_id::text)
FROM cargo.handling_attempt_quarantine q
WHERE q.id = a.quarantine_id;
ALTER TABLE cargo.handling_quarantine_replay_audit
    ALTER COLUMN request_id SET NOT NULL;
CREATE INDEX idx_handling_quarantine_replay_audit_request_id
    ON cargo.handling_quarantine_replay_audit (request_id, replayed_at);

GRANT SELECT, INSERT, UPDATE, DELETE ON cargo.handling_request_idempotency TO cargo_app;
