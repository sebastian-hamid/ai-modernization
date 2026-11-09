-- Initial PostgreSQL schema for the modernized Cargo Tracker candidate.
-- This migration is immutable after publication; use a new V<n> migration for changes.
CREATE SEQUENCE cargo.cargotracker_id_seq AS BIGINT START WITH 1 INCREMENT BY 1 NO CYCLE;
CREATE TABLE cargo.location (
    id BIGINT NOT NULL DEFAULT nextval('cargo.cargotracker_id_seq'),
    name VARCHAR(255), unlocode VARCHAR(255),
    CONSTRAINT pk_location PRIMARY KEY (id)
);
CREATE TABLE cargo.voyage (
    id BIGINT NOT NULL DEFAULT nextval('cargo.cargotracker_id_seq'),
    voyage_number VARCHAR(255),
    CONSTRAINT pk_voyage PRIMARY KEY (id)
);
CREATE TABLE cargo.cargo (
    id BIGINT NOT NULL DEFAULT nextval('cargo.cargotracker_id_seq'),
    calculated_at TIMESTAMP WITHOUT TIME ZONE, eta DATE,
    unloaded_at_dest BOOLEAN DEFAULT FALSE, misdirected BOOLEAN DEFAULT FALSE,
    routing_status VARCHAR(255), transport_status VARCHAR(255),
    next_expected_handling_event_type VARCHAR(255),
    next_expected_location_id BIGINT, next_expected_voyage_id BIGINT,
    current_voyage_id BIGINT, last_event_id BIGINT, last_known_location_id BIGINT,
    spec_arrival_deadline DATE, spec_destination_id BIGINT, spec_origin_id BIGINT,
    tracking_id VARCHAR(255),
    origin_id BIGINT,
    CONSTRAINT pk_cargo PRIMARY KEY (id),
    CONSTRAINT uq_cargo_tracking_id UNIQUE (tracking_id)
);
CREATE TABLE cargo.leg (
    id BIGINT NOT NULL DEFAULT nextval('cargo.cargotracker_id_seq'),
    load_time TIMESTAMP WITHOUT TIME ZONE, unload_time TIMESTAMP WITHOUT TIME ZONE,
    load_location_id BIGINT, unload_location_id BIGINT, voyage_id BIGINT, cargo_id BIGINT,
    CONSTRAINT pk_leg PRIMARY KEY (id)
);
CREATE TABLE cargo.handling_event (
    id BIGINT NOT NULL DEFAULT nextval('cargo.cargotracker_id_seq'),
    completion_date DATE, registration_date DATE, type VARCHAR(255),
    cargo_id BIGINT, location_id BIGINT, voyage_id BIGINT,
    CONSTRAINT pk_handling_event PRIMARY KEY (id)
);
CREATE TABLE cargo.carrier_movement (
    id BIGINT NOT NULL DEFAULT nextval('cargo.cargotracker_id_seq'),
    arrival_time TIMESTAMP WITHOUT TIME ZONE, departure_time TIMESTAMP WITHOUT TIME ZONE,
    arrival_location_id BIGINT, departure_location_id BIGINT, voyage_id BIGINT,
    CONSTRAINT pk_carrier_movement PRIMARY KEY (id)
);
-- Preserve imported legacy generator state; the application uses cargotracker_id_seq.
CREATE TABLE cargo.legacy_sequence_state (
    seq_name VARCHAR(50) NOT NULL, seq_count NUMERIC(15,0),
    CONSTRAINT pk_legacy_sequence_state PRIMARY KEY (seq_name)
);
ALTER TABLE cargo.cargo ADD CONSTRAINT fk_cargo_origin FOREIGN KEY (origin_id) REFERENCES cargo.location(id);
ALTER TABLE cargo.cargo ADD CONSTRAINT fk_cargo_spec_origin FOREIGN KEY (spec_origin_id) REFERENCES cargo.location(id);
ALTER TABLE cargo.cargo ADD CONSTRAINT fk_cargo_spec_destination FOREIGN KEY (spec_destination_id) REFERENCES cargo.location(id);
ALTER TABLE cargo.cargo ADD CONSTRAINT fk_cargo_last_known_location FOREIGN KEY (last_known_location_id) REFERENCES cargo.location(id);
ALTER TABLE cargo.cargo ADD CONSTRAINT fk_cargo_next_expected_location FOREIGN KEY (next_expected_location_id) REFERENCES cargo.location(id);
ALTER TABLE cargo.cargo ADD CONSTRAINT fk_cargo_current_voyage FOREIGN KEY (current_voyage_id) REFERENCES cargo.voyage(id);
ALTER TABLE cargo.cargo ADD CONSTRAINT fk_cargo_next_expected_voyage FOREIGN KEY (next_expected_voyage_id) REFERENCES cargo.voyage(id);
ALTER TABLE cargo.cargo ADD CONSTRAINT fk_cargo_last_event FOREIGN KEY (last_event_id) REFERENCES cargo.handling_event(id) DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE cargo.leg ADD CONSTRAINT fk_leg_load_location FOREIGN KEY (load_location_id) REFERENCES cargo.location(id);
ALTER TABLE cargo.leg ADD CONSTRAINT fk_leg_unload_location FOREIGN KEY (unload_location_id) REFERENCES cargo.location(id);
ALTER TABLE cargo.leg ADD CONSTRAINT fk_leg_voyage FOREIGN KEY (voyage_id) REFERENCES cargo.voyage(id);
ALTER TABLE cargo.leg ADD CONSTRAINT fk_leg_cargo FOREIGN KEY (cargo_id) REFERENCES cargo.cargo(id);
ALTER TABLE cargo.handling_event ADD CONSTRAINT fk_handling_event_cargo FOREIGN KEY (cargo_id) REFERENCES cargo.cargo(id) DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE cargo.handling_event ADD CONSTRAINT fk_handling_event_location FOREIGN KEY (location_id) REFERENCES cargo.location(id);
ALTER TABLE cargo.handling_event ADD CONSTRAINT fk_handling_event_voyage FOREIGN KEY (voyage_id) REFERENCES cargo.voyage(id);
ALTER TABLE cargo.carrier_movement ADD CONSTRAINT fk_carrier_movement_departure_location FOREIGN KEY (departure_location_id) REFERENCES cargo.location(id);
ALTER TABLE cargo.carrier_movement ADD CONSTRAINT fk_carrier_movement_arrival_location FOREIGN KEY (arrival_location_id) REFERENCES cargo.location(id);
ALTER TABLE cargo.carrier_movement ADD CONSTRAINT fk_carrier_movement_voyage FOREIGN KEY (voyage_id) REFERENCES cargo.voyage(id);
