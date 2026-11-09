#!/usr/bin/env bash
set -euo pipefail
umask 077
test "${DISPOSABLE_CANDIDATE_LAB:-}" = "true" || { echo "Disposable lab opt-in required" >&2; exit 2; }
# Generated per-run application-realm credentials are mounted read-only, never baked in.
cp /run/kan18/application-users.properties "$JBOSS_HOME/standalone/configuration/application-users.properties"
cp /run/kan18/application-roles.properties "$JBOSS_HOME/standalone/configuration/application-roles.properties"
# The import roots are private to the server OS identity; no web upload API writes here.
IMPORT_ROOT="$JBOSS_HOME/standalone/data/cargo-import"
for directory in "$IMPORT_ROOT/incoming" "$IMPORT_ROOT/archive" "$IMPORT_ROOT/failed"; do
  mkdir -p "$directory"
  chmod 700 "$directory"
done
# Restrict BatchPermission to the explicit worker identity and use that identity for JBeret jobs.
"$JBOSS_HOME/bin/jboss-cli.sh" --file=/opt/jboss/configure-batch-security.cli
"$JBOSS_HOME/bin/jboss-cli.sh" --file=/opt/jboss/notification-disposition.cli
exec "$JBOSS_HOME/bin/standalone.sh" -Dlab.candidate.disposable=true -Dlab.import.enabled="${LAB_IMPORT_ENABLED:-false}" -Dcargo.websocket.allowed-origins=http://ai-modernization-kan18:8080 -Dcargo.routing.credentials=/run/kan18/routing-client.properties -c standalone-full.xml -b 0.0.0.0
