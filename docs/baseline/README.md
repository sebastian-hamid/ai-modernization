# Legacy baseline documentation

Prepared 28 October 2026. These are AI-generated documents checked against pinned source and archived test evidence. They describe the existing application; approved future choices remain in the [modernization proposal](../../specifications/modernization-proposal.md).

- [Functional documentation](functional.md): users, terminology, workflows, rules, input/error behavior and evidence gaps.
- [Architecture documentation](architecture.md): deployment, layers, data relationships, asynchronous message flow, boundaries and migration risks.
- [Technical documentation](technical.md): API/batch/configuration contracts, reproduction, CI, troubleshooting and recovery limitations.
- [KAN-10 review](review-KAN-10.md): corrections, acceptance checklist and remaining review boundaries.
- [Verification manifest](verification.json): source commit/hashes, supporting file hashes, page inventory and checks performed for this documentation.

## Evidence levels and review scope

**Source-reviewed** means inspected code/configuration declares the behavior. **Recorded test evidence** means the existing archived run exercised it; it does not establish live health today. **Unverified** means no adequate execution evidence is available. **Target** means agreed future behavior, not an implemented feature.

The source checkout is pinned to `57fc7b32d2597e43b5e0d454e707e0146de5258a` and was clean before/after documentation. Citations use commit-specific upstream links; their corresponding local paths and SHA-256 hashes are in the manifest. Input identities, local links and key declarations were checked; live external links were not fetched and Mermaid diagrams were reviewed as text, not rendered.

Latest supporting application evidence is [Jenkins build 6](../../notes/evidence/coverage-review-2026-10-27/jenkins-build-6-summary.json), recorded 27 October: 134 reported application cases and 10 tooling checks pass. One domain test is empty. The separate desired-access gate fails; 13 anonymous operational surfaces were observed. No claim of exhaustive test, branch or security coverage is made.

This documentation pass did not start/restart services, mutate demo data, upgrade dependencies, implement target security or run a new CI build. Synced sources, original application code, credentials and existing work were preserved.

## Findings requiring follow-up

- Startup clears and reseeds records; persistence.xml enables schema creation. Durable business data and restart recovery are not established.
- Scheduled file import uses two-minute intervals despite a fifteen-minute comment; source config sets attempt-message TTL to one second. Batch execution and backlog/retry behavior need tests.
- RejectedRegistrationAttemptsQueue has a logging consumer but no producer path in JmsApplicationEvents; it is not evidence of verified dead-letter routing.
- Full browser workflows, CSV import, actual WebSocket messages, data schema export/index inventory, final retries, ownership/session/security behavior and measured performance remain incomplete.

See the [coverage review](../../notes/test-coverage-review.md) for the broader matrix. KAN-10 technical review results and corrections are recorded in review-KAN-10.md. The user reviewed and approved these baseline documents on 1 November 2026 and authorized committing/pushing them. This accepts the documentation with its explicitly stated gaps; it does not turn unverified behavior into test evidence or establish production readiness.

## Maintenance and next action

Maintain these baseline documents as a historical reference. Candidate behavior should be documented separately as changes are implemented; preserve a clear baseline/target distinction. For every change, update functional behavior, architecture impact, technical procedure and verification evidence as applicable. Mark assumptions and observed defects instead of silently promoting them to requirements.

Next under the agreed sequence: inventory entrypoints against the approved role policy, define failing desired-security tests, and verify a minimal Java 25/Jakarta EE 11 application on standard WildFly. Detailed numerical performance limits and runtime artifacts still need verification. No compatibility result is claimed by these documents.

## Documentation acceptance

User approval received 1 November 2026. The approved documents and their supporting verified tests/evidence are being versioned for GitHub publication. See [KAN-10](https://ai-modernization.atlassian.net/browse/KAN-10) for acceptance and the published revision reference.
