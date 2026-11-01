#!/usr/bin/env bash
set -euo pipefail
umask 077
test "${DISPOSABLE_CANDIDATE_LAB:-}" = "true" || { echo "Disposable lab opt-in required" >&2; exit 2; }
# Generated per-run application-realm credentials are mounted read-only, never baked in.
cp /run/kan18/application-users.properties "$JBOSS_HOME/standalone/configuration/application-users.properties"
cp /run/kan18/application-roles.properties "$JBOSS_HOME/standalone/configuration/application-roles.properties"
exec "$JBOSS_HOME/bin/standalone.sh" -Dlab.candidate.disposable=true -c standalone-full.xml -b 0.0.0.0
