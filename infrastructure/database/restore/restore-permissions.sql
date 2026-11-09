-- Run with psql -v restore_db=<target> -d <target> -f restore-permissions.sql
-- pg_restore --no-owner assigns restored objects to the restore connection role.
-- Transfer the application schema back to its migration owner before Flyway runs.
REVOKE CREATE ON DATABASE :"restore_db" FROM PUBLIC;
REVOKE TEMPORARY ON DATABASE :"restore_db" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"restore_db" TO schema_migrator, cargo_app;
ALTER SCHEMA cargo OWNER TO schema_migrator;
ALTER TABLE cargo.location OWNER TO schema_migrator;
ALTER TABLE cargo.voyage OWNER TO schema_migrator;
ALTER TABLE cargo.cargo OWNER TO schema_migrator;
ALTER TABLE cargo.leg OWNER TO schema_migrator;
ALTER TABLE cargo.handling_event OWNER TO schema_migrator;
ALTER TABLE cargo.carrier_movement OWNER TO schema_migrator;
ALTER TABLE cargo.legacy_sequence_state OWNER TO schema_migrator;
ALTER TABLE cargo.flyway_schema_history OWNER TO schema_migrator;
ALTER SEQUENCE cargo.cargotracker_id_seq OWNER TO schema_migrator;
GRANT USAGE ON SCHEMA cargo TO cargo_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA cargo TO cargo_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA cargo TO cargo_app;
