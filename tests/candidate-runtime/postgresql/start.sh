#!/usr/bin/env bash
set -euo pipefail
umask 077
test -r /run/secrets/app_password || { echo "PostgreSQL app credential is missing" >&2; exit 2; }
CARGO_APP_PASSWORD="$(cat /run/secrets/app_password)"
export CARGO_APP_PASSWORD
test -n "$CARGO_APP_PASSWORD" || { echo "PostgreSQL app credential is empty" >&2; exit 2; }
cp /run/secrets/application_users "$JBOSS_HOME/standalone/configuration/application-users.properties"
cp /run/secrets/application_roles "$JBOSS_HOME/standalone/configuration/application-roles.properties"
chmod 600 "$JBOSS_HOME/standalone/configuration/application-users.properties" "$JBOSS_HOME/standalone/configuration/application-roles.properties"
"$JBOSS_HOME/bin/jboss-cli.sh" --file=/opt/jboss/configure-postgresql-datasource.cli
exec "$JBOSS_HOME/bin/standalone.sh" -c standalone-full.xml -b 0.0.0.0 -Dlab.candidate.disposable=false -Dlab.import.enabled=false -Dcargo.websocket.allowed-origins=http://localhost:8082
