# Reproduce the KAN-27 local workload

This procedure reruns the workload and startup measurements in [`README.md`](README.md). It uses a per-run private directory, unique Compose project and image tag, isolated PostgreSQL volume, disposable candidate image with synthetic data seeding, and a local corrected legacy image. It does not target shared lab services or production.

## Requirements

- WSL2 Ubuntu with Docker Engine and Compose.
- Candidate sources and runtime files from this checkout.
- Corrected local GlassFish image `ai-modernization-glassfish:4.1-validator-fix`. Build it using [`../../docs/baseline/README.md`](../../docs/baseline/README.md) if needed.
- Host ports 8082 and 8083 available.

## Create unique run resources

Run these commands from the repository root in one WSL Bash shell and keep that shell open until cleanup. Strict mode makes command failures stop the procedure. The generated project, image tag, and private directory are unique to this run. Stop if either uniqueness check fails.

```bash
set -euo pipefail
KAN27_RUN_ID="$(date +%Y%m%d%H%M%S)-$$"
KAN27_PROJECT="kan27perf-${KAN27_RUN_ID}"
KAN27_IMAGE="ai-modernization-kan27-performance:${KAN27_RUN_ID}"
KAN27_PRIVATE="$(mktemp -d /tmp/kan27-private.XXXXXX)"
chmod 700 "$KAN27_PRIVATE"
KAN27_SECRET_DIR="$KAN27_PRIVATE/secrets"
COMPOSE_FILE=infrastructure/database/compose.yaml

if docker image inspect "$KAN27_IMAGE" >/dev/null 2>&1; then
  echo "Generated image tag already exists; stop and choose a new run ID" >&2; exit 1
fi
if docker ps -aq --filter "label=com.docker.compose.project=$KAN27_PROJECT" | grep -q . \
  || docker volume ls -q --filter "label=com.docker.compose.project=$KAN27_PROJECT" | grep -q . \
  || docker network ls -q --filter "label=com.docker.compose.project=$KAN27_PROJECT" | grep -q . \
  || docker volume inspect "${KAN27_PROJECT}_postgres_data" >/dev/null 2>&1 \
  || docker network inspect "${KAN27_PROJECT}_database" >/dev/null 2>&1 \
  || docker network inspect "${KAN27_PROJECT}_candidate-host-access" >/dev/null 2>&1; then
  echo "Generated Compose project resources already exist; stop and choose a new run ID" >&2; exit 1
fi
printf '%s\n%s\n' "$KAN27_PROJECT" "$KAN27_IMAGE" > "$KAN27_PRIVATE/.kan27-owned-run"
chmod 600 "$KAN27_PRIVATE/.kan27-owned-run"
```

## Build and start the disposable candidate

```bash
python3 notes/evidence/kan27-performance/prepare-secrets.py "$KAN27_SECRET_DIR"
docker build \
  -f notes/evidence/kan27-performance/Dockerfile.candidate \
  -t "$KAN27_IMAGE" .

export KAN22_SECRET_DIR="$KAN27_SECRET_DIR"
export KAN18_APP_IMAGE="$KAN27_IMAGE"

python3 notes/evidence/kan27-performance/measure_startup.py \
  --secret-dir "$KAN27_SECRET_DIR" \
  --project "$KAN27_PROJECT" \
  --output "$KAN27_PRIVATE/candidate-startup.json"
```

The startup runner creates a fresh Compose project and volume, waits for PostgreSQL, applies Flyway migrations, then waits for the protected catalogue endpoint to return its expected HTTP 401. The recorded time includes those steps but excludes image build time. The candidate image sets `lab.candidate.disposable=true` so the fresh database gets synthetic sample data. Never connect this fixture to a shared or existing database.

## Measure candidate

```bash
python3 notes/evidence/kan27-performance/measure.py \
  --base http://127.0.0.1:8082/cargo-tracker/ \
  --candidate \
  --containers "$KAN27_PROJECT-candidate-app-1,$KAN27_PROJECT-postgres-1" \
  --credentials-file "$KAN27_SECRET_DIR/application-passwords.json" \
  --label candidate-wildfly-postgresql \
  --samples 100 --warmups 20 --workers 5 \
  --output "notes/evidence/kan27-performance/candidate-rerun-${KAN27_RUN_ID}.json"
```

The runner validates the four sample IDs in each catalogue response and the `ABC123` public tracking result. Output contains raw request timings, summary percentiles, and coarse Docker stats; it does not include passwords.

Stop and remove only this run's candidate project and volume before measuring legacy:

```bash
docker compose -p "$KAN27_PROJECT" -f "$COMPOSE_FILE" --profile candidate-app down --volumes --remove-orphans
```

## Measure legacy

```bash
KAN27_LEGACY="${KAN27_PROJECT}-legacy"
if docker ps -a --format '{{.Names}}' | grep -Fxq "$KAN27_LEGACY"; then
  echo "Generated legacy container name already exists; stop and choose a new run ID" >&2; exit 1
fi
docker run -d --rm --name "$KAN27_LEGACY" \
  --publish 127.0.0.1:8083:8080 \
  ai-modernization-glassfish:4.1-validator-fix
```

Wait until `http://127.0.0.1:8083/cargo-tracker/rest/cargo` returns HTTP 200, then run:

```bash
python3 notes/evidence/kan27-performance/measure.py \
  --base http://127.0.0.1:8083/cargo-tracker/ \
  --containers "$KAN27_LEGACY" \
  --label legacy-glassfish-derby \
  --samples 100 --warmups 20 --workers 5 \
  --output "notes/evidence/kan27-performance/legacy-rerun-${KAN27_RUN_ID}.json"
docker stop "$KAN27_LEGACY"
```

Measure the two runtimes sequentially on the same WSL host to avoid local CPU and memory contention. Catalogue access differs: legacy is anonymous; candidate Operator login occurs outside the timed request. Compare these as the documented smoke workload, not as authorization-equivalent requests.

## Cleanup

Cleanup only when the private marker exists and its project/image values match the variables in the same shell:

```bash
if [[ ! -f "$KAN27_PRIVATE/.kan27-owned-run" ]] \
  || [[ "$(sed -n '1p' "$KAN27_PRIVATE/.kan27-owned-run")" != "$KAN27_PROJECT" ]] \
  || [[ "$(sed -n '2p' "$KAN27_PRIVATE/.kan27-owned-run")" != "$KAN27_IMAGE" ]]; then
  echo "Ownership marker missing or mismatched; refusing cleanup" >&2
  exit 1
fi
docker compose -p "$KAN27_PROJECT" -f "$COMPOSE_FILE" --profile candidate-app down --volumes --remove-orphans
if docker ps -a --format '{{.Names}}' | grep -Fxq "$KAN27_LEGACY"; then docker stop "$KAN27_LEGACY"; fi
rm -rf -- "$KAN27_PRIVATE"
docker image rm "$KAN27_IMAGE"
```

The unique project name and marker guard the destructive cleanup. If any step fails, preserve task-owned logs and use those same verified run values to clean up; do not substitute a generic or shared project name.

## Recorded raw reproduction runs

[`candidate-rerun-20261121.json`](candidate-rerun-20261121.json) and [`legacy-rerun-20261121.json`](legacy-rerun-20261121.json) contain 100 measured request durations per journey and load mode from a rerun using the checked-in harness. These are separate from the original aggregate-only baseline used to calculate the approved thresholds.
