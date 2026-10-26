#!/usr/bin/env bash
# Recover the fixed upstream source build without editing the upstream checkout.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
app_commit=57fc7b32d2597e43b5e0d454e707e0146de5258a
plugin_commit=60774367fba1287c2a838ac78799b32c563c0acf
theme_commit=db6195c272cd7b2567c60b4ed786e44bbecf5db0
image=maven@sha256:b9fac8295f9d342af5d815888dca1334b12833a84c870c260b88f31285c1ef3d
mkdir -p "$root/.work/m2" "$root/notes/evidence"
workspace="$(mktemp -d "$root/.work/recovered-baseline.XXXXXX")"
evidence="$(mktemp -d "$root/notes/evidence/recovered-baseline-$(date +%Y%m%d-%H%M%S).XXXXXX")"
printf 'Workspace: %s\nEvidence: %s\n' "$workspace" "$evidence"
trap 'printf "Stopped at line %s. Inspect evidence in %s\n" "$LINENO" "$evidence" >&2' ERR
mkdir "$workspace/source"
git -C "$root/experiments/legacy-cargotracker" archive "$app_commit" | tar -x -C "$workspace/source"
git clone --quiet https://github.com/primefaces/maven-jsf-plugin.git "$workspace/plugin"
git -C "$workspace/plugin" checkout --quiet "$plugin_commit"
git clone --quiet https://github.com/primefaces/themes.git "$workspace/themes"
git -C "$workspace/themes" checkout --quiet "$theme_commit"
run_maven() {
  local project="$1"
  shift
  docker run --rm --user "$(id -u):$(id -g)" -e MAVEN_CONFIG=/tmp/maven     -v "$workspace:/work" -v "$root/.work/m2:/m2"     -v "$root/infrastructure/legacy-maven-settings.xml:/settings.xml:ro"     -w "/work/$project" "$image" mvn -B -ntp -s /settings.xml -Dmaven.repo.local=/m2 "$@"
}
run_maven plugin -version > "$evidence/toolchain.txt" 2>&1
# Old build-plugin JUnit 4.4 is incompatible with the image's default Surefire.
# These are not application tests; skip this build-tool suite explicitly.
run_maven plugin -DskipTests install > "$evidence/jsf-plugin-build.log" 2>&1
run_maven themes -DskipTests -pl ui-lightness -am install > "$evidence/theme-build.log" 2>&1
run_maven source package > "$evidence/package.log" 2>&1
# Alter only skipTests in a separate test POM. Preserve the original package POM.
python3 - "$workspace/source" <<'PY'
from pathlib import Path
import sys
source=Path(sys.argv[1])
text=(source/"pom.xml").read_text()
assert "<skipTests>true</skipTests>" in text, "Upstream test configuration changed"
(source/"domain-tests-pom.xml").write_text(text.replace("<skipTests>true</skipTests>","<skipTests>false</skipTests>"))
PY
run_maven source -f domain-tests-pom.xml   -Dtest=CargoTest,ItineraryTest,RouteSpecificationTest,HandlingEventTest,HandlingHistoryTest   test > "$evidence/domain-tests.log" 2>&1
cp -r "$workspace/source/target/surefire-reports" "$evidence/"
diff -u "$workspace/source/pom.xml" "$workspace/source/domain-tests-pom.xml" > "$evidence/test-pom-overlay.diff" || test "$?" -eq 1
python3 "$root/infrastructure/record-legacy-provenance.py" "$root" "$workspace" "$evidence"
printf 'Package and domain tests passed. Evidence: %s\nWAR: %s\n' "$evidence" "$workspace/source/target/cargo-tracker.war"
tail -12 "$evidence/domain-tests.log"
