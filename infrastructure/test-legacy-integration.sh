#!/usr/bin/env bash
# Run the four active upstream Arquillian booking tests against the isolated server.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
container=ai-modernization-cargotracker
docker exec "$container" test -f /tmp/cargo-tracker-deployed
workspace="$(mktemp -d "$root/.work/runtime-tests.XXXXXX")"
evidence="$(mktemp -d "$root/notes/evidence/runtime-integration-$(date +%Y%m%d-%H%M%S).XXXXXX")"
git -C "$root/experiments/legacy-cargotracker" archive 57fc7b32d2597e43b5e0d454e707e0146de5258a | tar -x -C "$workspace"
python3 - "$workspace" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1])
text=(root/"pom.xml").read_text()
assert "<skipTests>true</skipTests>" in text
(root/"integration-tests-pom.xml").write_text(text.replace("<skipTests>true</skipTests>","<skipTests>false</skipTests>"))
PY
set +e
docker run --rm --network "container:$container" --user "$(id -u):$(id -g)"   -e MAVEN_CONFIG=/tmp/maven -v "$root/.work:/work"   -v "$root/infrastructure/legacy-maven-settings.xml:/settings.xml:ro"   -w "/work/$(basename "$workspace")"   maven@sha256:b9fac8295f9d342af5d815888dca1334b12833a84c870c260b88f31285c1ef3d   mvn -B -ntp -s /settings.xml -Dmaven.repo.local=/work/m2   -Dorg.apache.maven.user-settings=/settings.xml -f integration-tests-pom.xml   -Dtest=BookingServiceTest test > "$evidence/booking-integration.log" 2>&1
result=$?
set -e
if [ -d "$workspace/target/surefire-reports" ]; then cp -r "$workspace/target/surefire-reports" "$evidence/"; fi
docker logs "$container" > "$evidence/server.log" 2>&1
tail -18 "$evidence/booking-integration.log"
printf 'Integration exit: %s; evidence: %s\n' "$result" "$evidence"
exit "$result"
