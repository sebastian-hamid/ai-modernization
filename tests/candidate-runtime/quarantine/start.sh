#!/usr/bin/env bash
set -euo pipefail
umask 077
for secret in app_password application_users application_roles; do
  test -r "/run/secrets/$secret" || { echo "Required candidate secret is missing" >&2; exit 2; }
done
CARGO_APP_PASSWORD="$(cat /run/secrets/app_password)"
export CARGO_APP_PASSWORD
cp /run/secrets/application_users "$JBOSS_HOME/standalone/configuration/application-users.properties"
cp /run/secrets/application_roles "$JBOSS_HOME/standalone/configuration/application-roles.properties"
chmod 600 "$JBOSS_HOME/standalone/configuration/application-users.properties" "$JBOSS_HOME/standalone/configuration/application-roles.properties"
"$JBOSS_HOME/bin/jboss-cli.sh" --file=/opt/jboss/configure-postgresql-datasource.cli
"$JBOSS_HOME/bin/jboss-cli.sh" --file=/opt/jboss/notification-disposition.cli
candidate_hostname="${LAB_CANDIDATE_HOSTNAME:-localhost}"
exec "$JBOSS_HOME/bin/standalone.sh" -c standalone-full.xml -b 0.0.0.0 \
  -Dlab.candidate.disposable=false -Dlab.import.enabled=false \
  -Dcargo.websocket.allowed-origins="http://${candidate_hostname}:8080"
