-- Query indexes plus ID high-water reconciliation after data is imported between V1 and V2.
-- This migration never seeds demo/business rows.
CREATE INDEX idx_cargo_origin_id ON cargo.cargo(origin_id);
CREATE INDEX idx_cargo_spec_destination_id ON cargo.cargo(spec_destination_id);
CREATE INDEX idx_leg_cargo_id ON cargo.leg(cargo_id);
CREATE INDEX idx_handling_event_cargo_dates ON cargo.handling_event(cargo_id, completion_date, registration_date);
CREATE INDEX idx_carrier_movement_voyage_id ON cargo.carrier_movement(voyage_id);
WITH ids AS (
    SELECT id FROM cargo.location
    UNION ALL SELECT id FROM cargo.voyage
    UNION ALL SELECT id FROM cargo.cargo
    UNION ALL SELECT id FROM cargo.leg
    UNION ALL SELECT id FROM cargo.handling_event
    UNION ALL SELECT id FROM cargo.carrier_movement
), high_water AS (
    SELECT GREATEST(
        COALESCE((SELECT MAX(id) FROM ids), 0),
        COALESCE((SELECT MAX(seq_count)::BIGINT FROM cargo.legacy_sequence_state), 0),
        0
    ) AS id
)
SELECT setval('cargo.cargotracker_id_seq', GREATEST(id, 1), id > 0) FROM high_water;
