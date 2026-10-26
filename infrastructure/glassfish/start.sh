#!/usr/bin/env bash
set -euo pipefail
admin=/opt/glassfish4/bin/asadmin
"$admin" start-domain --verbose domain1 &
server_pid=$!
trap '"$admin" stop-domain domain1; wait "$server_pid"' TERM INT
for attempt in $(seq 1 90); do
  if "$admin" list-applications > /tmp/readiness.log 2>&1; then
    "$admin" deploy --name cargo-tracker --contextroot cargo-tracker /opt/cargo-tracker.war
    touch /tmp/cargo-tracker-deployed
    wait "$server_pid"
    exit $?
  fi
  if ! kill -0 "$server_pid" 2>/dev/null; then
    wait "$server_pid"
    exit 1
  fi
  sleep 2
done
cat /tmp/readiness.log
exit 1
