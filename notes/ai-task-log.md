# AI assistance task log

## 28 October 2026 — Legacy baseline documentation

- Objective: produce functional, architecture and technical descriptions of the unchanged application before modernization.
- AI outputs: three baseline documents, index, source/evidence verification manifest and links from repository notes/README.
- Review/corrections: checked cited source paths and key declarations; classified runtime results as historical evidence; highlighted actual two-minute schedule versus fifteen-minute comment, destructive seed initialization, one-second attempt TTL, and absence of a demonstrated rejection-queue producer. Did not infer successful browser, batch, retry or recovery behavior from source alone.
- Verification: pinned checkout identity/cleanliness, cited input hashes, local-link existence, key declaration checks, recorded Jenkins counts and repository whitespace check. No new application tests/deployments were run for this documentation-only change.
- Human decisions: previously approved documentation scope and verification approach; these documents have not yet received user acceptance review.
- Human review/rework time: unavailable; no value inferred.
- Exact task elapsed time and attributable usage cost: unavailable; no value inferred. No hours-saved claim.
- Tool/model: file/command tools; model identifier not reliably available for this task record.
- Open work: full browser workflows, CSV execution, WebSocket messages, physical DDL/index inventory, queue failure disposition and target runtime compatibility. See baseline documentation and coverage review.

## 28 October 2026 — Jira backlog publication

- User approved AI Team (KAN) and the prepared 6 epics/21 work items. Used the Atlassian spec-to-backlog skill with the existing local specification and approved breakdown.
- Inspected existing issues/create permissions and issue types; created epics before children, sequentially captured keys, preserved KAN-1 through KAN-3 and project settings.
- Mapped unavailable Bug/Spike types to labeled Tasks. Included acceptance criteria, dependencies and source/evidence context in descriptions; repository documents remain local pending publication.
- Read back all 27 imported issues and verified counts, summaries, types and epic parents. All initially To Do and unassigned; no retrospective completion, due dates or estimates supplied. Formal dependency links were not created.
- Saved specifications/jira-issue-map.json and updated backlog/proposal. Human review/rework time, attributable cost and exact task elapsed time: unavailable; no savings claim.

## 28 October 2026 — KAN-10 documentation review

- Read Jira criteria and moved task to In Progress, then In Review after technical corrections and evidence recording; stakeholder acceptance remains pending.
- Reviewed all three documents and original source/evidence manifests. Corrected direct repository/event paths in architecture, generated-ID wording, tracking behavior, relationship wording and batch skip/filter limits.
- Verified 39 source citations and 35 local links, clean pinned source, manifest hashes and archived CI counts (134 application cases, 10 tooling checks). Kept the old manifest and wrote review-KAN-10.md plus review-results.json; added Jira comment 10000.
- No application build, mutation, deployment or service restart; no claim of new browser/security execution. Source-only/unverified paths remain labeled.
- Human acceptance: pending. Human review/rework time, attributable usage cost and exact elapsed task time: unavailable; no savings claim.

## 1 November 2026 — Approved documentation publication

- User confirmed documentation review/approval and authorized commit/push. Recorded acceptance without converting source-only gaps into runtime evidence.
- Reviewed pending documentation plus supporting tests/evidence, scanned for credential patterns (no matches), verified all executed pipeline input hashes against passing Jenkins build 6, and re-ran 10 tooling checks successfully. Historical source remains clean; synced sources untouched.
- Publishing the approved documentation with supporting verified baseline/test artifacts and prior local baseline/skill commits. No application deployment, security remediation or new full CI run is claimed.
- Human review duration, rework time, exact elapsed time and attributable cost unavailable; no savings claim.

## 1 November 2026 — KAN-12 entrypoint/policy inventory

- Inventoried 25 page/template files, 45 active callback/navigation occurrences, two flow descriptors, three REST resource families, one WebSocket, six background boundaries, four application-service groups, 41 static/image files and five private metadata/source-note files.
- Produced specifications/access-policy-map.md and access-policy-inventory.json, plus scripts/build-access-inventory.py. Classified every web file and hashed 175 source/configuration files; verified REST/WebSocket declarations and repeat generation determinism.
- Applied approved human roles, separate machine-worker/OS/broker/deployment authority, and default deny. Found separate mapFrame.html, mixed read/write dashboards, protected public/track path and unresolved bindings.
- Recorded enforcement and future candidate test location/groups for each surface; no executable candidate security test or enforcement was implemented. Historical source/services were unchanged.
- Human review/acceptance of this mapping pending. Review/rework duration, exact elapsed time and attributable cost unavailable; no savings claim.

## 1 November 2026 — Standard separate-agent review workflow

- User approved separate-agent review for substantive code/documentation. Created docs/agent-review-workflow.md and root AGENTS.md; linked from README and recorded the approved proposal decision.
- Separate reviewer /root/review_workflow_policy used fresh context and read-only checks. Verdict: no material findings. Scope excludes the separate pending KAN-12 mapping review; records are in notes/agent-reviews/2026-11-01-workflow-review.md and JSON.
- Recorded user KAN-12 approval and still-pending independent review in Jira comment 10003; recorded workflow adoption on KAN-11 in comment 10004.
- Human review/rework time, attributable cost and exact elapsed time unavailable. No historical review or savings claims. Changes remain local/uncommitted; no publication performed.

## 1 November 2026 — Reviewed workflow and KAN-12 publication

- User explicitly requested commit/push. Separate reviewer /root/review_kan12_publication found P2 relative-navigation role mismatch in ACTION-11/21/22; corrected target resolution/role intersection and regenerated JSON, Markdown matrix and validation evidence. Reviewer recheck: no remaining material findings.
- Verified deterministic output, exact reviewed hashes, complete source census, local links, clean historical checkout, whitespace and credential-pattern scan (no matches). No new full application/CI/runtime security test was needed for this source/design publication.
- Recorded separate review evidence and user approval; KAN-12 moved Done. Included previously independently reviewed workflow policy and AGENTS.md in the authorized publication checkpoint.
- Human review/rework time, attributable cost and exact elapsed time unavailable; no savings claim.

## 1 November 2026 — KAN-13 runtime compatibility spike

- Created isolated minimal WAR/container probes with pinned standard WildFly 42 and Maven/JDK digests, stable compiler/API/WAR versions. Official WildFly image included older JDK25.0.4.1; assembled current Temurin25.0.5 from the pinned build image and verified actual runtime/bytecode. No silent fallback or formal TCK claim.
- Executed actual JPA/H2, JMS consumer, Faces/CDI, batch COMPLETED and basic local role checks. First run exposed uncontrolled REST response from an EJB role denial; added HTTP POST role constraint, retaining EJB checks. Preserved first failed result; corrected fresh runs pass19.
- Separate reviewer /root/review_kan13_runtime found no material compatibility issue and a non-material pre-cleanup initialization edge case. Fixed it, added one Docker-mocked fault-injection regression, reran19 and obtained focused recheck: no remaining findings. Review hashes/evidence recorded.
- Temporary container/realm files removed; existing legacy app stays healthy, controller/agent unchanged, original source clean. Full application migration/security/PrimeFaces/PostgreSQL/Flyway/restart/performance remain future work. Files are local, not pushed during this task.
- Actual runtime/startup/toolchain observations and task review records saved; human review/rework time, exact elapsed effort and attributable cost unavailable. No invented savings.

## 1 November 2026 — KAN-13 publication

- User explicitly authorized commit/push. Rechecked separate-review hashes, all runtime build-input identities, 19 passing recorded checks, private-file cleanup and historical source cleanliness. The focused harness regression passed again; credential-pattern scan found no matches.
- Included spike source, pinned container/build configuration, bounded ADR, independent review records, preserved first failure and sanitized final evidence. No new application deployment or full CI run was performed for publication.
- Earlier local/uncommitted notes describe the pre-publication state; this checkpoint publishes the reviewed artifacts. Exact commit/remote verification reference is recorded in Jira. Publication bookkeeping is non-semantic and does not alter reviewed build inputs.

- Publication whitespace check found only extra blank lines at EOF in several reviewed spike inputs. Preserved their exact tested bytes and checked other whitespace errors with the blank-at-EOF cosmetic warning excluded for this check only; no repository-wide setting changed.
