---
name: legacy-java-baseline
description: Recover and verify a reproducible build, runtime, and behavior baseline for an existing legacy Java application before modernization. Use for historical Java or Java EE dependencies, runtime compatibility failures, or baseline CI setup; not for ordinary greenfield Java development.
---

# Legacy Java Baseline

Establish what the existing application builds and does before changing its behavior. Use the project's own scripts and runbooks when they exist. Adapt the process to the requested milestone; using this skill does not authorize publishing, changing unrelated services, or modernizing the application.

## Establish the actual environment

Locate the working repository and read its instructions and setup notes. Treat synced reference copies as references rather than the working checkout. Separate historical claims from current command output.

In Windows/WSL environments, identify which shell and filesystem execute each tool. Inspect the resolved Java, compiler and Maven paths, Java versions, JAVA_HOME and Maven runtime. A command can accidentally resolve through an imported Windows PATH. Shell Java settings do not configure Java in a container or CI agent. Derive the JDK root from the selected compiler rather than assuming an architecture-specific directory.

Inspect the source commit, build configuration and original server requirements before choosing the legacy toolchain. Keep the modern development JDK separate where necessary; an old source target or application server may need a different JDK. Do not prescribe a particular JDK, server, container platform, port or directory to every project.

## Preserve and recover the build

Pin the upstream source revision and build from a separate checkout or exported copy when the original must remain unchanged. Record selected image digests and tool versions.

For dependency failures, distinguish missing artifacts, obsolete repository URLs, certificate failures and compiler incompatibility. Check exact artifact coordinates at publisher archives or trusted existing caches first. Keep TLS verification and repository protections enabled; use narrowly scoped repository settings rather than weakening global configuration.

If a published binary is unavailable but its official release source is recoverable, a rebuild may establish a recovered source baseline. Pin that source and document the rebuild. Do not claim byte-identical equivalence to the missing published binary. Do not silently substitute newer dependencies or label a modified build as the unchanged original.

Record artifact coordinates, observed source URL or release commit, SHA-256 and recovery method. Maven Resolver can append context hashes to repository IDs in local cache records; resolve those IDs accurately and report unknown provenance rather than guessing a default origin. An observed hash pins recovered bytes but is not a publisher signature.

When exact recovery is blocked, preserve the failure and identify the missing artifact or decision. Any necessary substitutions belong in a separately identified compatibility experiment.

## Verify tests actually execute

Inspect test annotations, framework inheritance, lifecycle plugins, profiles, test dependencies and skip settings. A successful package command may have skipped every test. An explicit literal in a POM may require a documented test-only overlay rather than a command-line property override.

Run viable domain tests before server-dependent tests. Keep temporary POM changes separate from application code and record their diff. Report tests, failures, errors and skips; identify empty test methods and unfinished classes rather than counting them as meaningful coverage.

Collect reports even when the build fails. Operational checksum and result guards must still execute under optimized Python or equivalent modes that can disable language assertions.

## Reproduce the runtime and behavior

Recover the intended server distribution and record its provenance. Preserve a stock-runtime failure before applying a compatibility correction. Check publisher documentation or an upstream issue for a matching cause; keep the correction narrow, reversible and explicitly identified. A corrected runtime must not be described as unmodified.

Use an isolated local runtime where appropriate, respecting occupied ports and existing services. Verify startup data sources, schema/sample data and messaging requirements instead of assuming a separate database service is needed. Identify any startup routine that clears or reseeds data before restarting an existing instance.

Check observable workflows, not just server startup. For asynchronous operations, verify the eventual state change as well as HTTP acceptance. With historical sample dates or randomized routes, record those dependencies and assert meaningful invariants; do not silently change fixtures, clocks or randomness to force a pass. Distinguish HTTP/server-side checks from browser JavaScript, WebSocket and other untested behavior.

## Carry the baseline into CI

Adapt verified commands to the user's CI system. Prefer a separate build agent and the agent's own disposable test runtime rather than running builds on a controller or modifying a shared demonstration instance. Separate the JDK needed for agent connectivity from the JDK needed by the application.

Do not introduce a host Docker socket or privileged container just to reuse Docker-wrapped developer commands. Native build tools and a temporary server inside an ordinary agent can be sufficient. If an existing project needs container-enabled CI, choose its isolation arrangement deliberately within the authorized scope.

For local source snapshots, use an exact input set, account for removed files and record hashes. Preserve the mounted directory when a Docker bind mount depends on it. Keep credentials out of the snapshot. Label snapshot-based jobs accurately; they are not SCM-triggered builds. Validate ownership before replacing an existing same-named job or node, keep connection secrets private and deactivate one-time registration scripts after use.

Archive test reports, logs, build outputs and provenance. Clean up the temporary runtime on failures as well as success. Exclude local caches, connection data and bulky raw diagnostics from source versioning while preserving useful review evidence.

## Handoff

Update repository notes with verified state, exact reproduction commands, source/tool/runtime identities, documented deviations and remaining coverage gaps. Keep machine paths, accounts, current service URLs, artifact versions and changing install state in those project records rather than adding them to this reusable skill.

State what passed and what remains blocked. Version the reviewed setup when requested; publishing it or adding remote triggers remains a separate action unless already authorized.
