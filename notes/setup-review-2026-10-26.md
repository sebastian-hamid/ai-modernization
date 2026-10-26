# Setup review — 26 October 2026

Release: 0.1.0. Local Git tag: baseline-v0.1.0. This versions the lab setup and verification tooling, not a modernized application release. GitHub publication and SCM-triggered builds are outside this change.

## Scope
Reviewed the recovery/build scripts, runtime correction, Docker Compose configuration, Jenkins agent registration, pipeline, provenance records, source snapshot refresh and verification evidence. The upstream Cargo Tracker checkout and synced ChatGPT references remain untouched. The standalone app remains on localhost:8081.

## Findings resolved
- Snapshot refresh previously retained deleted scripts. It now maintains the exact source file set without replacing the Docker bind-mounted directory, rejects symlinks and records input hashes. CI verifies those hashes before running builds.
- Python assertions could disappear under PYTHONOPTIMIZE. Runtime checksum/patch guards, test-result checks and smoke checks now use explicit failures.
- Failed Maven domain tests could lose their JUnit reports. Reports are now collected in a finally block so Jenkins can publish failures.
- Maven Resolver appends context hashes to repository IDs. The provenance recorder previously fell back to a false Maven Central URL for nine Eclipse artifact records. It now recognizes the suffix and refuses unknown origins. Matching historical local records are annotated with their previously recorded URL and corrected origin; artifact hashes are unchanged. Build 1's original Jenkins archive is preserved.
- Interrupted runtime downloads could leave a partial archive at the final path. Downloads now use a partial file and verify its hash before replacing the cache entry.
- Jenkins registration previously accepted any same-named WorkflowJob and wrote the node secret before restricting permissions. It now validates the existing lab job/node before mutation and writes its secret atomically with private permissions.
- Added explicit ignored paths for CI artifacts and large verbose runtime logs. Those logs remain available locally; concise reports, provenance and review evidence are versioned.

## Validation
Eight regression checks exercise:
1. Deleted snapshot inputs disappear while the bind directory remains the same.
2. Source symlinks are rejected.
3. Snapshot symlinks cannot lead writes/removal outside the managed directory.
4. Optimized Python still rejects non-local smoke targets before network access.
5. Optimized Python rejects a corrupt GlassFish archive.
6. Maven context-suffixed repository IDs map to the actual Eclipse publisher URL.
7. Unknown artifact origins cause failure rather than invented provenance.
8. A failed domain run preserves its JUnit report.

The checks pass on the WSL Python runtime and inside the actual Jenkins agent. The first Jenkins review run exposed a test-only traceback-format difference in the agent's newer Python; that test now examines the final exception instead of incidental traceback source text. The application checks were not bypassed.

[Reviewed Jenkins build 3](http://localhost:8080/job/ai-modernization-baseline/3/) finished SUCCESS in 153.108 seconds. All eight tooling checks, 28 reported application tests and HTTP workflow checks passed. The archived source hashes match the reviewed files. Results are recorded in [review summary](evidence/jenkins-review-summary.json). The pipeline also verifies the original 24 domain tests and four booking integration tests, plus HTTP workflow checks. One historical domain test remains an empty TODO.

A targeted scan of files selected for versioning found no actual private keys or access tokens. The apparent password-pattern match is the agent startup script reading its connection secret from a file; no secret value is present. Private connection data, caches, nested source clones and raw large server logs remain excluded.

## Skill recommendation
A focused legacy-java-baseline skill would be useful for future legacy Java modernization labs. Its reusable guidance should cover:
- Pin upstream source and distinguish a recovered source build from byte-identical published artifacts.
- Recover dependencies from identifiable publisher sources; retain hashes and avoid fabricated provenance.
- Separate the modern toolchain from the legacy build/runtime.
- Isolate the runtime and CI agent, preserve a failing stock-runtime record and document exact compatibility corrections.
- Verify that tests actually execute; distinguish domain tests, integration tests, empty tests and unfinished test classes.
- Check asynchronous state changes, not just accepted HTTP responses, and account for historical dates and randomized routes.
- Preserve reproducible commands and evidence before modifying application behavior.

Keep lab-specific paths, user/account information, URLs, current status, image digests and artifact versions in repository documentation and scripts. They should not become universal skill requirements. Start with a concise instruction-only skill that points to each project's own commands; add shared scripts only after a second lab demonstrates real reuse.

This review assesses the skill design; it does not install or create a personal skill.
