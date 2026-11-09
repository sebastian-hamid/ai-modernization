#!/bin/sh
set -eu
sql_literal() {
    escaped=$(printf '%s' "$1" | sed "s/'/''/g")
    printf "'%s'" "$escaped"
}
app_password=$(cat /run/secrets/app_password)
migrator_password=$(cat /run/secrets/migrator_password)
app_literal=$(sql_literal "$app_password")
migrator_literal=$(sql_literal "$migrator_password")
unset app_password migrator_password
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set ON_ERROR_STOP=1 <<SQL
CREATE ROLE schema_migrator LOGIN PASSWORD $migrator_literal
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
CREATE ROLE cargo_app LOGIN PASSWORD $app_literal
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
GRANT CONNECT ON DATABASE cargotracker TO schema_migrator, cargo_app;
REVOKE CREATE ON DATABASE cargotracker FROM PUBLIC;
REVOKE TEMPORARY ON DATABASE cargotracker FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
CREATE SCHEMA cargo AUTHORIZATION schema_migrator;
REVOKE ALL ON SCHEMA cargo FROM PUBLIC;
GRANT USAGE ON SCHEMA cargo TO cargo_app;
ALTER ROLE schema_migrator SET search_path = cargo, public;
ALTER ROLE cargo_app SET search_path = cargo, public;
SQL
unset app_literal migrator_literal
