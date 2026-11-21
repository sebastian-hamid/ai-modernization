# KAN-27 local performance baseline

**Status:** initial latency p95 review triggers agreed; reproduction package checked in; startup/resource thresholds remain unapproved.  
**Measured:** 2026-11-21 (Europe/Bratislava local date).  
**Scope:** disposable local runtimes only; no production-like load claim.

## Environment

- Host: WSL2 Ubuntu 24.04 on Linux kernel 6.18.58.1-microsoft-standard-WSL2; Docker Engine 29.9.1, Compose 5.6.0. Docker reported 12 CPUs and 15.55 GiB available to containers; WSL reported 15 GiB total and about 12 GiB available. No per-container CPU or memory limits were configured.
- Legacy: corrected GlassFish 4.1 baseline image `ai-modernization-glassfish:4.1-validator-fix`, image ID `sha256:899f3ae0a00cc80fd9e8dd49d9104da4baf4aad81167754ac51c8c3b7a160e84`, Java 8 and Derby.
- Candidate: task-only image based on the repository candidate runtime, with a disposable-fixture startup override, image ID `sha256:f6fe1db0ba065c126be14168994e8ba65842559a3c43620e8fa0454b29ea8ced`, WildFly 42.0.0.Final, Java 25 and PostgreSQL 18.6.
- Each runtime used the same four synthetic tracking IDs: `ABC123`, `DEF789`, `JKL567`, and `MNO456`. Legacy ran in fresh task-named containers and candidate ran in a task-specific Compose project and database volume. No shared Jenkins, KAN-18, source, or database was used or altered.

## Workload and method

Two read-only user journeys were measured after 20 warm-up iterations per workload:

1. Cargo catalogue read: `GET /rest/cargo`. The legacy endpoint was anonymous; the candidate endpoint required an Operator session, established before timing each sample. The request and response body were checked, including all four seeded records.
2. Public tracking lookup: load the public tracking form, submit `ABC123`, and validate the result. This is a GET plus POST round trip, timed together.

For each journey and runtime, 100 sequential samples and 100 samples spread across five concurrent workers were collected. Percentiles use the nearest-rank method. Three legacy cold starts from new containers reached HTTP 200 for the catalogue in 25.27, 22.35 and 23.39 seconds (mean 23.67s). A separate legacy workload run recorded another fresh-container startup of 22.578 seconds to the same HTTP 200 readiness, with all four synthetic IDs verified. Candidate app readiness after PostgreSQL was already healthy and migrations were already applied was initially observed at 18.166 seconds; three additional fresh-app-container recreations reached the expected protected-endpoint HTTP 401 in 16.189, 16.750 and 17.181 seconds, timed from the Compose command returning (excluding that command overhead). All four app-only values exclude PostgreSQL boot and migrations. A fresh full-stack startup including PostgreSQL health, migrations and Compose command overhead, but excluding image build, reached candidate readiness in 29.788 seconds (one sample).

## Latency results

Times in milliseconds; catalogue and tracking journeys should be interpreted separately because their access and request paths differ.

| Runtime | Journey | Samples | Sequential p50 / p95 | Five-worker p50 / p95 |
|---|---|---:|---:|---:|
| Legacy GlassFish / Derby | Catalogue GET (anonymous) | 100 each | 14.90 / 20.65 | 27.34 / 40.40 |
| Candidate WildFly / PostgreSQL | Catalogue GET (Operator session already established) | 100 each | 13.65 / 16.41 | 17.62 / 32.78 |
| Legacy GlassFish / Derby | Public tracking GET + POST | 100 each | 56.39 / 81.51 | 108.25 / 142.20 |
| Candidate WildFly / PostgreSQL | Public tracking GET + POST | 100 each | 39.63 / 52.61 | 81.37 / 100.06 |

### Approved initial regression review policy

The user approved this four-record synthetic workload as an initial local regression check and approved a review trigger when a candidate journey's p95 exceeds its recorded candidate baseline by more than 20%. Apply each threshold to the matching journey and concurrency mode, using the 20 sequential warm-ups per journey before timing, 100 timed samples per mode, five workers for the concurrent mode, and the same local runtime setup. Crossing a threshold triggers investigation and review; it is not an automatic release failure or a service-level objective.

| Candidate journey | Mode | Baseline p95 | Review trigger above 120% |
|---|---|---:|---:|
| Catalogue GET (Operator session already established) | Sequential | 16.410 ms | >19.692 ms |
| Catalogue GET (Operator session already established) | Five workers | 32.780 ms | >39.336 ms |
| Public tracking form GET + POST | Sequential | 52.610 ms | >63.132 ms |
| Public tracking form GET + POST | Five workers | 100.060 ms | >120.072 ms |

These limits cover only latency p95 for this initial workload. No startup or resource regression thresholds were approved. Full descriptive statistics and coarse container-stat snapshots are in [`summary.json`](summary.json). A checked-in rerun harness and raw samples are available in [`candidate raw run`](candidate-rerun-20261121.json) and [`legacy raw run`](legacy-rerun-20261121.json). The rerun candidate p95 values (catalogue 16.95/34.55 ms; tracking 57.17/103.85 ms, sequential/five-worker) remained below the approved review triggers.

## Resource observations

Container memory was about 698 MiB before the legacy workload and 761 MiB after it; candidate app memory ranged about 761–796 MiB during measured work, while PostgreSQL ranged about 51–80 MiB. Docker stats were sampled approximately every 0.5 seconds, but the workload windows produced only 1–6 snapshots per journey. CPU is instantaneous and spiky; these readings and memory deltas are coarse observations, not peak or capacity measurements. They must not be used as production sizing values.

## Interpretation and limits

- The repository now contains the workload and startup runners, disposable image recipe, private-credential generator, detailed [`reproduction procedure`](REPRODUCE.md), and raw results from a second run. A corrected legacy image must be available locally. It remains a small, uncontrolled benchmark: there is one host, a tiny four-record synthetic dataset, no network latency, limited startup repetitions, and coarse resource sampling.
- The candidate and legacy are distinct stacks, so the measurements show observed behavior of these tested versions; they do not isolate the effect of a single modernization change.
- Candidate catalogue measurements exclude authentication establishment time, while legacy catalogue access is anonymous. Do not infer equivalent authorization behavior from latency.
- Candidate app-only readiness has four samples after PostgreSQL migrations; full-stack startup including PostgreSQL health, migrations and Compose overhead has one 29.788-second observation. There is not enough repetition to characterize startup variability. The exact full-stack result is in [`candidate full-stack startup`](candidate-fullstack-startup-20261121.json).
- The user approved the initial four-record workload and the latency p95 review triggers below. Startup and resource thresholds remain unapproved. These triggers call for investigation, not an automatic pass/fail decision.

## Cleanup and safety

The legacy throwaway containers were removed after measurement. The candidate app and PostgreSQL ran only in uniquely named, task-owned Compose projects with private fixture credentials. All task-owned projects, volumes, containers, credentials, and temporary image tags were removed after measurement. No files under `sources/` or `experiments/legacy-cargotracker/` were edited.
