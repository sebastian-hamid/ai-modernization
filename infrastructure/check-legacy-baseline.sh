#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_repo="$root/experiments/legacy-cargotracker"
commit=57fc7b32d2597e43b5e0d454e707e0146de5258a
image=maven@sha256:b9fac8295f9d342af5d815888dca1334b12833a84c870c260b88f31285c1ef3d
git -C "$source_repo" cat-file -e "$commit^{commit}"
mkdir -p "$root/.work" "$root/notes/evidence"
workspace="$(mktemp -d "$root/.work/legacy-baseline.XXXXXX")"
git -C "$source_repo" archive "$commit" | tar -x -C "$workspace"
log="$root/notes/evidence/legacy-package-rerun-$(date +%Y%m%d-%H%M%S).log"
set +e
docker run --rm --user "$(id -u):$(id -g)" -e MAVEN_CONFIG=/tmp/maven   -v "$workspace:/workspace" -w /workspace "$image"   mvn -B -ntp -Dmaven.repo.local=/workspace/.m2 package 2>&1 | tee "$log"
result=${PIPESTATUS[0]}
set -e
printf 'Build exit: %s; log: %s; workspace: %s\n' "$result" "$log" "$workspace"
exit "$result"
