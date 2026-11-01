# Proposed Jira backlog

Prepared 28 October 2026 from the approved modernization proposal and verified baseline findings. **Published 28 October 2026 to AI Team (KAN) at https://ai-modernization.atlassian.net:** 6 epics and 21 work items created and read back to verify types and epic parents. IDs below remain local planning references; actual Jira keys are mapped at the end and in jira-issue-map.json. No assignees, due dates, estimates or explicit priorities were assigned; Jira supplied its project defaults.

## Working agreement

Jira adoption is approved. Use Jira to track work, acceptance criteria and confirmed bugs; keep code and versioned documentation in Git and execution evidence in Jenkins. Link issues to source commits, documents and test evidence. AI may draft issue content, but do not mark work Done without supporting evidence. Import/create once, record the resulting Jira keys, and inspect for duplicates before retrying.

Completed setup/build/test recovery should be captured as historical context linked to existing evidence, not fabricated as previously tracked Jira work or estimated retrospectively. The documentation artifacts are produced but still need acceptance review. Proposed states below are descriptive local planning states, not assumed Jira workflow statuses.

## Proposed epics

| Local reference | Epic | Scope |
| --- | --- | --- |
| EP-DOC | Documentation | Baseline/candidate functional, architecture and technical docs plus AI evidence. |
| EP-SEC | Security | Entry-point policy, desired tests, local accounts, roles, API/WebSocket/session controls. |
| EP-PLAT | Platform and UI | Compatibility spike, Java/Jakarta/WildFly migration, Faces/PrimeFaces and browser workflows. |
| EP-DB | PostgreSQL and Flyway | Physical schema/mapping, versioned migrations, persistent storage and data checks. |
| EP-QA | Resilience and verification | Validation, concurrency, CSV, messaging, disconnect behavior and performance. |
| EP-OPS | Delivery and handoff | CI source integration, restart/recovery/rollback and acceptance/agent instructions. |

## Proposed execution sequence

1. Review baseline documentation; map access policy and verify minimal runtime compatibility.
2. Define desired security tests and implement access controls.
3. Complete platform and UI modernization.
4. Migrate persistence using PostgreSQL/Flyway.
5. Complete resilience/performance/recovery checks and handoff; documentation and AI evidence continue throughout.

The sequence is approved; task decomposition/dependency details below are a starting plan, not extra approved architecture decisions. Performance limits require agreement after measurement; external publication remains separate.

## Backlog summary

| Local ID | Epic | Type | Summary | Current evidence/state |
| --- | --- | --- | --- | --- |
| DOC-01 | Documentation | Task | Review and accept legacy baseline documentation | Produced; acceptance review pending |
| DOC-02 | Documentation | Task | Maintain candidate documentation and AI task evidence | Planned |
| SEC-01 | Security | Task | Map every entrypoint and action to the approved access policy | Ready to refine |
| PLAT-01 | Platform and UI | Spike | Verify minimal Java 25 / Jakarta EE 11 / standard WildFly compatibility | Ready to refine |
| SEC-02 | Security | Task | Define desired-access tests for anonymous, role and session cases | Planned |
| SEC-03 | Security | Story | Implement local identities and authorization on candidate surfaces | Planned |
| BUG-01 | Security | Bug | Close confirmed anonymous operational reads and writes | Confirmed in historical evidence |
| BUG-02 | Security | Bug | Restrict tracking WebSocket access and permitted origins | Confirmed handshake exposure |
| PLAT-02 | Platform and UI | Story | Modernize the application platform and dependencies | Planned |
| PLAT-03 | Platform and UI | Story | Modernize Faces/PrimeFaces and verify browser workflows | Planned |
| BUG-03 | Platform and UI | Bug | Fix broken tracking view and uncontrolled direct-link errors | Confirmed in historical evidence |
| DB-01 | PostgreSQL and Flyway | Task | Inventory legacy schema and define PostgreSQL mapping | Planned |
| DB-02 | PostgreSQL and Flyway | Story | Introduce PostgreSQL and versioned Flyway migrations | Planned |
| QA-01 | Resilience and verification | Task | Close domain, booking, handling and CSV coverage gaps | Planned |
| BUG-04 | Resilience and verification | Bug | Correct agreed input-validation and error-response defects | Confirmed examples; desired rules to refine |
| QA-02 | Resilience and verification | Task | Verify messaging failure, retry and expiration behavior | Planned |
| BUG-05 | Resilience and verification | Bug | Reproduce and fix abrupt WebSocket disconnect failures | Exploratory observation; reproduction required |
| QA-03 | Resilience and verification | Task | Measure performance and agree regression thresholds | Planned |
| OPS-01 | Delivery and handoff | Story | Verify durable restart, backup/restore and rollback | Planned |
| CI-01 | Delivery and handoff | Task | Connect reviewed source to Jenkins SCM execution | Planned |
| OPS-02 | Delivery and handoff | Task | Complete acceptance review and reusable agent instructions | Planned |

## Reviewable issue descriptions

### DOC-01: Review and accept legacy baseline documentation

**Type:** Task. **Epic:** Documentation. **Planning state:** Produced; acceptance review pending.

Review docs/baseline functional, architecture and technical documents against pinned source and archived evidence. Correct gaps and mark source-only versus tested behavior.

**Acceptance criteria:** All three documents reviewed; unsupported claims corrected; explicit gaps retained; review recorded.

**Dependencies / ordering:** —.

### DOC-02: Maintain candidate documentation and AI task evidence

**Type:** Task. **Epic:** Documentation. **Planning state:** Planned.

Update functional, architecture and technical documentation for each modernization increment; record AI output, human corrections and verification.

**Acceptance criteria:** Each increment links current docs and evidence; unavailable time/cost marked unavailable; no unmeasured savings claims.

**Dependencies / ordering:** Ongoing.

### SEC-01: Map every entrypoint and action to the approved access policy

**Type:** Task. **Epic:** Security. **Planning state:** Ready to refine.

Inventory pages, JSF actions, REST, WebSocket, internal routing calls, scheduled batch and filesystem input. Apply approved roles and anonymous boundary.

**Acceptance criteria:** Every entrypoint has allowed roles and enforcement/test location; internal callers and non-HTTP triggers explicitly covered.

**Dependencies / ordering:** DOC-01.

### PLAT-01: Verify minimal Java 25 / Jakarta EE 11 / standard WildFly compatibility

**Type:** Spike. **Epic:** Platform and UI. **Planning state:** Ready to refine.

Build and deploy a minimal isolated candidate WAR; select exact maintenance releases and image digest; check persistence, messaging, Faces, batch and security capability.

**Acceptance criteria:** Reproducible build/start evidence and compatibility decision recorded; no silent fallback or change to the historical runtime.

**Dependencies / ordering:** DOC-01.

### SEC-02: Define desired-access tests for anonymous, role and session cases

**Type:** Task. **Epic:** Security. **Planning state:** Planned.

Create candidate expectations separate from insecure historical characterization. Include successful role actions, direct access, expired/logout sessions and denied mutation effects.

**Acceptance criteria:** Tests reproduce current gaps; expected 401/403 or appropriate page login navigation documented; denied writes checked for queued/persisted changes.

**Dependencies / ordering:** SEC-01.

### SEC-03: Implement local identities and authorization on candidate surfaces

**Type:** Story. **Epic:** Security. **Planning state:** Planned.

Configure WildFly-managed local accounts, sessions and explicit Reader/Operator/Administrator mappings; protect all mapped surfaces and internal calls.

**Acceptance criteria:** Authorized actions pass; anonymous/wrong-role attempts fail; CSRF/session handling verified where relevant; credentials absent from Git/images.

**Dependencies / ordering:** SEC-02, PLAT-01.

### BUG-01: Close confirmed anonymous operational reads and writes

**Type:** Bug. **Epic:** Security. **Planning state:** Confirmed in historical evidence.

Baseline permits cargo monitoring, direct admin views and a state-changing handling report without authentication. Desired security gate fails.

**Acceptance criteria:** Candidate denies unauthorized reads/writes while allowing approved roles; evidence links to coverage-review results; no data/queue change from denied reports.

**Dependencies / ordering:** SEC-03.

### BUG-02: Restrict tracking WebSocket access and permitted origins

**Type:** Bug. **Epic:** Security. **Planning state:** Confirmed handshake exposure.

Baseline accepts anonymous upgrade with an unrelated Origin; actual message leakage was not tested.

**Acceptance criteria:** Reject unauthorized upgrade; enforce permitted origins and role visibility; verify logout/expiry and authorized message delivery.

**Dependencies / ordering:** SEC-03.

### PLAT-02: Modernize the application platform and dependencies

**Type:** Story. **Epic:** Platform and UI. **Planning state:** Planned.

Migrate candidate source/build to the agreed Java/Jakarta/WildFly target; preserve domain behavior and port security controls.

**Acceptance criteria:** Fresh candidate build/deployment passes intended functional and security suites; dependencies and compatibility changes pinned/documented.

**Dependencies / ordering:** SEC-03.

### PLAT-03: Modernize Faces/PrimeFaces and verify browser workflows

**Type:** Story. **Epic:** Platform and UI. **Planning state:** Planned.

Update compatible UI dependencies, selectively replace legacy mobile screens and automate booking, routing, destination change, tracking and mobile flows.

**Acceptance criteria:** Real browser happy/negative paths pass; direct navigation behaves intentionally; UI workflow and technical docs updated.

**Dependencies / ordering:** PLAT-02.

### BUG-03: Fix broken tracking view and uncontrolled direct-link errors

**Type:** Bug. **Epic:** Platform and UI. **Planning state:** Confirmed in historical evidence.

admin/track references missing destinationCoordinates; direct eventLogger lacks FlowScoped context; missing/unknown cargo IDs cause 500 on tested admin links.

**Acceptance criteria:** Valid navigation works; unknown/missing IDs yield controlled responses; flow bypass has defined behavior; access checks apply first.

**Dependencies / ordering:** PLAT-03.

### DB-01: Inventory legacy schema and define PostgreSQL mapping

**Type:** Task. **Epic:** PostgreSQL and Flyway. **Planning state:** Planned.

Export/review physical Derby schema, keys/indexes, dates and relationships; separate demo seeding from durable application startup.

**Acceptance criteria:** Reviewed mapping and data conversion rules; no assumption that ORM annotations equal complete physical DDL.

**Dependencies / ordering:** PLAT-02.

### DB-02: Introduce PostgreSQL and versioned Flyway migrations

**Type:** Story. **Epic:** PostgreSQL and Flyway. **Planning state:** Planned.

Use separate persistent database container, immutable SQL migrations and dedicated migration credentials/step; restrict application credentials.

**Acceptance criteria:** Fresh and upgrade paths tested; data/date/transaction checks pass; no automatic deployed schema mutation or seed deletion; secrets external.

**Dependencies / ordering:** DB-01.

### QA-01: Close domain, booking, handling and CSV coverage gaps

**Type:** Task. **Epic:** Resilience and verification. **Planning state:** Planned.

Replace empty domain TODO; add negative booking, invalid inputs, replay/order/concurrency and batch validation tests.

**Acceptance criteria:** Meaningful assertions cover prioritized matrix; intentional defect corrections tracked separately from historical contracts.

**Dependencies / ordering:** PLAT-03, DB-02.

### BUG-04: Correct agreed input-validation and error-response defects

**Type:** Bug. **Epic:** Resilience and verification. **Planning state:** Confirmed examples; desired rules to refine.

Tests show malformed enums/location/time values returning 500, lenient dates and loading after claim. Document business decisions before changing each behavior.

**Acceptance criteria:** Approved desired rules have failing-before/passing-after tests; invalid inputs receive controlled responses; unaffected business workflows preserved.

**Dependencies / ordering:** QA-01.

### QA-02: Verify messaging failure, retry and expiration behavior

**Type:** Task. **Epic:** Resilience and verification. **Planning state:** Planned.

Investigate 1000-ms attempt TTL, final retry/dead-letter/rejection behavior, backlog and replay/idempotency. Source rejection consumer is not evidence of a working rejection route.

**Acceptance criteria:** Observed failure disposition and recovery documented; acceptance/loss policy agreed; no claim of exactly-once behavior without evidence.

**Dependencies / ordering:** DB-02.

### BUG-05: Reproduce and fix abrupt WebSocket disconnect failures

**Type:** Bug. **Epic:** Resilience and verification. **Planning state:** Exploratory observation; reproduction required.

An exploratory disposable runtime showed stale-session send errors affecting cargo inspection. Establish a repeatable candidate test before selecting a fix.

**Acceptance criteria:** Abrupt disconnect does not prevent unrelated cargo processing; graceful close and actual message delivery also pass.

**Dependencies / ordering:** PLAT-02.

### QA-03: Measure performance and agree regression thresholds

**Type:** Task. **Epic:** Resilience and verification. **Planning state:** Planned.

Define representative workload, dataset and environment; measure baseline startup, latency and resources before proposing limits.

**Acceptance criteria:** Measurements reproducible; numerical thresholds explicitly agreed; candidate results reported without invented equivalence.

**Dependencies / ordering:** DOC-01; candidate comparison after DB-02.

### OPS-01: Verify durable restart, backup/restore and rollback

**Type:** Story. **Epic:** Delivery and handoff. **Planning state:** Planned.

Keep legacy demo separate; reproduce candidate restarts and rehearse restore/rollback including data and configuration compatibility. Historical disposable deployment restart failure remains a recorded finding.

**Acceptance criteria:** Restart retains data; restoration verified; rollback rehearsal passes; limitations and exact commands documented.

**Dependencies / ordering:** DB-02.

### CI-01: Connect reviewed source to Jenkins SCM execution

**Type:** Task. **Epic:** Delivery and handoff. **Planning state:** Planned.

Review and version pending repository changes; replace candidate local snapshots with explicit SCM checkout/trigger only after publication is arranged. Preserve historical job.

**Acceptance criteria:** Build records exact Git revision; reviewed triggers and isolated candidate agent; tests/security gates/archive work; no credentials exposed.

**Dependencies / ordering:** Reviewed source and agreed GitHub publication.

### OPS-02: Complete acceptance review and reusable agent instructions

**Type:** Task. **Epic:** Delivery and handoff. **Planning state:** Planned.

Review agreed completion criteria, documentation, functional/security tests, recovery, performance, AI evidence and remaining limitations.

**Acceptance criteria:** Acceptance and remaining limitations explicitly recorded; step-by-step agent instructions have inputs, actions, checks, recovery and stop conditions.

**Dependencies / ordering:** All required preceding increments.

## Evidence and destination

- [Approved proposal](modernization-proposal.md)
- [Baseline documentation](../docs/baseline/README.md)
- [Coverage and access findings](../notes/test-coverage-review.md)
- [Jenkins build 6 evidence](../notes/evidence/coverage-review-2026-10-27/jenkins-build-6-summary.json)
- [Brief work history](../notes/work-completed-brief.md)

**Destination confirmed:** AI Team (KAN), explicitly approved by the user. Atlassian is connected. Existing KAN-1 through KAN-3 and project workflow/configuration were preserved. If Spike or another proposed issue type is unavailable, map to an available type without altering the project's workflow or permissions. Use issue links for dependencies according to available link types; do not assume a CSV importer or custom field schema. Jira links to local files will need accessible Git URLs or appropriately scoped document attachments after publication is arranged; raw WSL paths alone are not portable Jira evidence links. Do not expose credentials, private runtime logs or unintended project data.

## Created Jira items

All 27 imported items were verified in To Do, with 21 children correctly parented to six epics. KAN supports Epic/Story/Task/Subtask; planned Bug items were created as Tasks with the bug label, and the Spike as a Task with the spike label. Dependencies are included in issue descriptions; formal blocking links have not been created. No work was marked complete retroactively.

| Local reference | Jira item | Type | Parent |
| --- | --- | --- | --- |
| EP-DOC | [KAN-4](https://ai-modernization.atlassian.net/browse/KAN-4) | Epic | — |
| EP-SEC | [KAN-5](https://ai-modernization.atlassian.net/browse/KAN-5) | Epic | — |
| EP-PLAT | [KAN-6](https://ai-modernization.atlassian.net/browse/KAN-6) | Epic | — |
| EP-DB | [KAN-7](https://ai-modernization.atlassian.net/browse/KAN-7) | Epic | — |
| EP-QA | [KAN-8](https://ai-modernization.atlassian.net/browse/KAN-8) | Epic | — |
| EP-OPS | [KAN-9](https://ai-modernization.atlassian.net/browse/KAN-9) | Epic | — |
| DOC-01 | [KAN-10](https://ai-modernization.atlassian.net/browse/KAN-10) | Task | KAN-4 |
| DOC-02 | [KAN-11](https://ai-modernization.atlassian.net/browse/KAN-11) | Task | KAN-4 |
| SEC-01 | [KAN-12](https://ai-modernization.atlassian.net/browse/KAN-12) | Task | KAN-5 |
| PLAT-01 | [KAN-13](https://ai-modernization.atlassian.net/browse/KAN-13) | Task | KAN-6 |
| SEC-02 | [KAN-14](https://ai-modernization.atlassian.net/browse/KAN-14) | Task | KAN-5 |
| SEC-03 | [KAN-15](https://ai-modernization.atlassian.net/browse/KAN-15) | Story | KAN-5 |
| BUG-01 | [KAN-16](https://ai-modernization.atlassian.net/browse/KAN-16) | Task | KAN-5 |
| BUG-02 | [KAN-17](https://ai-modernization.atlassian.net/browse/KAN-17) | Task | KAN-5 |
| PLAT-02 | [KAN-18](https://ai-modernization.atlassian.net/browse/KAN-18) | Story | KAN-6 |
| PLAT-03 | [KAN-19](https://ai-modernization.atlassian.net/browse/KAN-19) | Story | KAN-6 |
| BUG-03 | [KAN-20](https://ai-modernization.atlassian.net/browse/KAN-20) | Task | KAN-6 |
| DB-01 | [KAN-21](https://ai-modernization.atlassian.net/browse/KAN-21) | Task | KAN-7 |
| DB-02 | [KAN-22](https://ai-modernization.atlassian.net/browse/KAN-22) | Story | KAN-7 |
| QA-01 | [KAN-23](https://ai-modernization.atlassian.net/browse/KAN-23) | Task | KAN-8 |
| BUG-04 | [KAN-24](https://ai-modernization.atlassian.net/browse/KAN-24) | Task | KAN-8 |
| QA-02 | [KAN-25](https://ai-modernization.atlassian.net/browse/KAN-25) | Task | KAN-8 |
| BUG-05 | [KAN-26](https://ai-modernization.atlassian.net/browse/KAN-26) | Task | KAN-8 |
| QA-03 | [KAN-27](https://ai-modernization.atlassian.net/browse/KAN-27) | Task | KAN-8 |
| OPS-01 | [KAN-28](https://ai-modernization.atlassian.net/browse/KAN-28) | Story | KAN-9 |
| CI-01 | [KAN-29](https://ai-modernization.atlassian.net/browse/KAN-29) | Task | KAN-9 |
| OPS-02 | [KAN-30](https://ai-modernization.atlassian.net/browse/KAN-30) | Task | KAN-9 |

## KAN-10 review progress (28 October 2026)
Source/evidence review completed with documentation corrections; KAN-10 is In Review for stakeholder acceptance. See [review record](../docs/baseline/review-KAN-10.md). No historical application test gaps or security findings were closed by this documentation-only review. Initial import statuses above are historical snapshots.

## Documentation acceptance (1 November 2026)
The user reviewed and approved the baseline documentation and authorized Git commit/push. The 28 October In Review entries above are historical; KAN-10 acceptance and publication are recorded in Jira. Remaining security/runtime/test gaps stay open.

## KAN-12 policy mapping (1 November 2026)
Entrypoint/action mapping and source census completed; KAN-12 is In Review. See [access-policy-map.md](access-policy-map.md) and its validation evidence. New mapping files are local pending review/publication. No security remediation or candidate test execution is claimed.

## KAN-12 acceptance and publication (1 November 2026)
User approval and separate-agent review are complete. One P2 navigation-role inconsistency was corrected and rechecked; no material findings remain. KAN-12 is Done for the policy inventory/design task. The map, generator and validation evidence are included in this publication checkpoint, together with the standard review workflow and review records. Earlier In Review/uncommitted entries above are historical snapshots. No runtime security remediation is claimed.

## KAN-13 compatibility spike (1 November 2026)
KAN-13 is Done: minimal standard WildFly42/Java25.0.5/JakartaEE11 WAR passed19 capability checks and one cleanup regression, with separate-agent review/recheck complete. See [spike](../spikes/kan13-runtime/README.md) and [ADR](../docs/architecture-decisions/0001-kan13-runtime-foundation.md). Full CargoTracker migration/security/PrimeFaces/PostgreSQL/Flyway remain unproven. New spike artifacts remain local and uncommitted; no publication was performed in this task.

## KAN-13 publication checkpoint (1 November 2026)
The user authorized commit/push of the independently reviewed spike and evidence. Included artifacts are listed in the KAN-13 README/ADR; earlier local/uncommitted statements above are historical. The published commit reference is recorded on KAN-13.
