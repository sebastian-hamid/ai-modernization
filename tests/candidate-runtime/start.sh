#!/usr/bin/env bash
set -euo pipefail
umask 077
test "${DISPOSABLE_CANDIDATE_LAB:-}" = "true" || { echo "Disposable lab opt-in required" >&2; exit 2; }
# Generated per-run application-realm credentials are mounted read-only, never baked in.
cp /run/kan18/application-users.properties "$JBOSS_HOME/standalone/configuration/application-users.properties"
cp /run/kan18/application-roles.properties "$JBOSS_HOME/standalone/configuration/application-roles.properties"
# Local attach/JMX observations require broker cumulative management counters. No remote JMX listener.
"$JBOSS_HOME/bin/jboss-cli.sh" --commands="embed-server --server-config=standalone-full.xml --std-out=discard,/subsystem=messaging-activemq/server=default:write-attribute(name=jmx-management-enabled,value=true),stop-embedded-server" >/dev/null
exec "$JBOSS_HOME/bin/standalone.sh" -Dlab.candidate.disposable=true -Dcargo.websocket.allowed-origins=http://ai-modernization-kan18:8080 -Dcargo.routing.credentials=/run/kan18/routing-client.properties -c standalone-full.xml -b 0.0.0.0
