# AI modernization lab

Setup baseline **0.1.0**, reviewed 26 October 2026. Local release tag: baseline-v0.1.0.

Windows 11 + WSL2 Ubuntu development environment, local Jenkins and a preserved legacy Cargo Tracker checkout.

- [Verified setup and remaining checks](notes/setup-status.md)
- [Legacy baseline findings and next steps](notes/legacy-baseline.md)
- [Running application, runtime recovery and integration tests](notes/legacy-runtime.md)
- [Passing Jenkins baseline pipeline](notes/jenkins-baseline.md)
- [Setup review and versioning](notes/setup-review-2026-10-26.md)
- [Reusable legacy Java baseline skill](notes/skills.md)
- Jenkins job: http://localhost:8080/job/ai-modernization-baseline/
- Application: http://localhost:8081/cargo-tracker/
- Jenkins: http://localhost:8080/
- Compose configuration: infrastructure/compose.yaml
- Existing application source: ignored experiments/legacy-cargotracker

Modern development uses Java 21 and Ubuntu Maven. The legacy build experiment uses a digest-pinned Java 8/Maven container. The recovered source baseline packages successfully. Five domain test classes report 24 passing tests (one is an empty TODO). GlassFish deployment, four Arquillian booking integration tests and HTTP tracking/routing/asynchronous-handling smoke checks pass. The runtime includes the documented HK2-277 metadata correction; browser JavaScript and other coverage gaps are listed in the runtime notes.

Reproduce dependency recovery, packaging and domain tests from Ubuntu:
    bash infrastructure/recover-legacy-baseline.sh

The earlier infrastructure/check-legacy-baseline.sh preserves the initial unrecovered-build experiment.

Keep credentials and Jenkins home data out of Git.
