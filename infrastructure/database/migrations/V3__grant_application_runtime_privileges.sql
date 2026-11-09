-- Grant only runtime application objects after V1/V2 are present.
-- Keep Flyway history and legacy_sequence_state private to schema_migrator.
GRANT SELECT, INSERT, UPDATE, DELETE ON cargo.location, cargo.voyage, cargo.cargo, cargo.leg, cargo.handling_event, cargo.carrier_movement TO cargo_app;
GRANT USAGE, SELECT, UPDATE ON SEQUENCE cargo.cargotracker_id_seq TO cargo_app;
