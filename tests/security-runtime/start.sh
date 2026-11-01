#!/usr/bin/env bash
set -euo pipefail
umask 077
# Generated per-run application-realm credentials are mounted read-only, never baked in.
cp /run/kan15/application-users.properties "$JBOSS_HOME/standalone/configuration/application-users.properties"
cp /run/kan15/application-roles.properties "$JBOSS_HOME/standalone/configuration/application-roles.properties"
exec "$JBOSS_HOME/bin/standalone.sh" -c standalone-full.xml -b 0.0.0.0
