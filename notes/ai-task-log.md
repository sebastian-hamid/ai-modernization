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

## 1 November 2026 — KAN-14 desired access tests

- Defined generated desired-role/session cases separately from insecure historical characterization. Added strict identity, status, no-leak and database/queue/business-audit effect assertions; missing candidate adapters block the gate.
- Executed 16 assertion-engine unit checks and fresh disposable historical gap probe: 2 public-page PASS, 8 security FAIL. Candidate gate: 502 BLOCKED, 0 PASS, exit 2. Runtime removed; shared historical application/Jenkins and read-only source preserved.
- Defined direct/AJAX replay, logout/expiry, scoped machine authorities and further scenario expansion requirements in tests/security/README.md. Runtime identity/session implementation remains KAN-15; no production security or full browser verification claimed.
- Separate reviewer found socket-revocation and public no-leak false-pass paths; corrected with regressions. Recheck confirmed both fixes, 16 passing unit checks, deterministic generation and matching hashes; no remaining material definition/oracle findings. Literal denied-write queue/persistence execution remains incomplete; ticket stays In Review pending KAN-15 candidate/observers. No publication performed. Human review duration, effort and attributable cost unavailable; no savings claim.

## 1 November 2026 — KAN-14 publication

- User authorized commit/push. Verified all eight reviewed input hashes and reran 16 passing assertion-engine checks. Published desired-access definitions, sanitized evidence and independent review records; no application runtime or security success claimed.
- KAN-14 remains In Review: real denied-write database/queue observations require candidate authentication and independent observers. Earlier local/uncommitted statements describe the pre-publication checkpoint. No runtime rerun or service changes during publication.

## 1 November 2026 — KAN-15 local identity/session foundation (in progress)

- Implemented reusable container-login, session CSRF/logout, explicit HTTP path roles and CDI method roles under candidate/security. Kept integration test WAR under tests/security-runtime separate from Cargo Tracker.
- Fresh pinned WildFly/Java25 fixture passes 49 runtime checks: actual local accounts/roles, session ID rotation, CSRF, direct service-role denial, logout replay and real server idle expiry. Three cleanup regressions pass (partial secret initialization, Docker log failure and container removal failure). Runtime/private realm files removed; historical source/demo/Jenkins preserved.
- This does not implement full KAN-15 or unblock KAN-14: actual Cargo Tracker candidate bootstrap (overlaps KAN-18), all callbacks/EJB/machine boundaries, WebSocket revocation and real database/queue/business-audit observers remain required. KAN-15 stays In Progress. See candidate/security/README.md; independent review/recheck complete with no remaining material foundation findings after cleanup correction. No commit/push. Human effort/review time/cost unavailable; no savings claim.

## 1 November 2026 — KAN-15 foundation publication

- User authorized commit/push. Verified all20 independently reviewed input hashes,49 passing recorded runtime checks, runtime/private-file cleanup and reran three cleanup regressions successfully. Included security library, separate fixture, sanitized evidence and independent review records; raw logs/private files excluded.
- KAN-15 remains In Progress and KAN-14 remains502 BLOCKED pending actual application integration and independent database/queue observers. Earlier local/uncommitted statements describe the pre-publication checkpoint. No new runtime deployment or full CI run during publication.

## 1 November 2026 — KAN-18 real candidate bootstrap / KAN-15 integration

- Exported 218 original source/test/resource/license files from pinned legacy commit into candidate/cargotracker, retaining original hashes and license. Added the existing ten-case factory characterization test. Migrated Jakarta APIs/build, current PrimeFaces adapters and standard REST/JMS/JPA declarations; historical source remains clean.
- Integrated reviewed local login/session/HTTP roles and EJB API/worker roles for real monitoring/handling only. Other operational routes deny by default pending UI/action/routing/WebSocket integration. First real runtime exposed failed MDB delivery authorization; preserved failure, corrected narrow internal delivery permission and retained worker authority.
- Final fresh disposable run: 34 domain tests (one inherited empty TODO), 35 runtime PASS and three cleanup regressions PASS. Actual Operator/Administrator JMS-driven persisted cargo changes verified; no independent denied-write DB/queue/audit absence claimed. Runtime/private files removed, historical demo HTTP200 and Jenkins preserved.
- Separate reviewer /root/review_kan18_bootstrap inspected source/provenance/limited security and independently ran cleanup regressions; fixed its non-material stale-context concern with fresh build directories. Final independent recheck verified218 original and237 current hashes,35 runtime results and3 independently rerun cleanup tests; no remaining material findings for this limited bootstrap. Both KAN-18/KAN-15 remain In Progress; KAN-14 still502 BLOCKED. See candidate/cargotracker/README.md and notes/evidence/kan-18-candidate. Local only, no commit/push. Human effort/review time/cost unavailable; no savings claim.

## 1 November 2026 — KAN-18 bootstrap publication

- User authorized commit/push. Verified all237 independently reviewed current input hashes and final evidence hashes; confirmed35 passing runtime checks and34 domain cases (one original empty TODO); reran three cleanup regressions successfully. Private realm files absent; only source, selected documentation and sanitized evidence included.
- Independent review/recheck found no remaining material findings for this limited bootstrap. KAN-15/KAN-18 remain In Progress and KAN-14 remains502 BLOCKED. Earlier local/uncommitted statements describe the pre-publication checkpoint. No runtime redeployment/full CI run during publication.
- Publication checks found inherited trailing/EOF whitespace and four upstream CRLF files. Preserved exact reviewed bytes via four file-specific Git text exceptions; all237 staged input hashes match review. Whitespace check passed with only trailing/EOF cosmetic warnings excluded for this invocation. This non-semantic publication bookkeeping used the workflow's lighter check; reviewed application/test inputs unchanged.

## 1 November 2026 — KAN-19 real browser workflow increment

- Implemented real Faces/PrimeFaces cargo list/details/booking/destination pages over existing business services, with Reader reads and Operator/Administrator mutations. Added HTTP+facade/EJB roles, session CSRF and exact static-resource/library policy. Routing/tracking/legacy mobile logger remain disabled; no full KAN-19 acceptance claimed.
- Browser testing exposed lazy DTO collection access, templated metadata placement and shared empty itinerary persistence ownership. Corrected transaction boundary, metadata client facet and per-cargo empty itinerary. Independent reviewer found an assigned-empty route fixture conflict; corrected to valid nonempty fixtures without changing three status assertions and added a distinct-empty NOT_ROUTED regression. Preserved sanitized failures.
- Final fresh run:30 Chromium assertions PASS,35 actual application runtime checks PASS,35 domain cases PASS (one inherited empty TODO),six mocked cleanup regressions PASS. Operator and Administrator create real cargos/change destinations and separate Reader sessions see persistence. Tests cover Reader links/forged POSTs, CSRF, invalid calendar/same-location inputs, controlled invalid IDs, resource bypass and tested mobile details viewport.
- Task-owned app/browser/private network removed; memory-only browser credentials and private realm files removed. Historical app HTTP200, original source clean and Jenkins preserved. Full KAN-14 independent DB/queue/audit absence still unverified;502 candidate definitions remain BLOCKED. KAN-15/KAN-18/KAN-19 stay In Progress.
- Independent review/recheck complete: all250 hashes match,30 browser/35 application/35 domain results inspected and six cleanup regressions independently rerun; no remaining material findings for this bounded increment. Local uncommitted/unpushed. Human effort/review time/cost unavailable; no savings claim. See docs/candidate/browser-workflows.md and notes/evidence/kan-19-browser.

## 1 November 2026 — KAN-19 publication and standing authorization

- User authorized this commit/push and future publication after independent agent approval. Recorded that exact authorization in AGENTS.md; this factual permission bookkeeping does not waive independent review, required checks or separate deployment restrictions.
- Verified all250 reviewed input hashes and three final evidence hashes;30 browser/35 application/35 domain passing results (one inherited empty TODO) retained. Reran six mocked cleanup tests successfully. Independent reviewer approved this bounded increment after the routing-fixture correction/recheck; no remaining material findings.
- KAN-19/KAN-15/KAN-18 remain In Progress; full routing/live tracking/mobile and independent effect observers remain open. Earlier local/uncommitted statements describe the pre-publication checkpoint. No runtime redeployment/full CI run for publication.

## 1 November 2026 — KAN-19 routing and scoped internal identity

- Integrated actual sample route request/selection/assignment/rerouting in Faces with server-held choices, O/A HTTP/facade/EJB permissions, session CSRF and current-spec validation for committed stale candidates. Kept legacy demonstration planner explicit; no real timetable optimization claim.
- Preserved internal HTTP with a separate native WildFly RoutingService account, private per-run client credentials, fixed loopback endpoint, redirects disabled/timeouts/client close. Machine Basic authentication exists only at graph API; credentials are never forwarded from humans or provided to browser fixtures. Per-request identity/session cleanup and third-secret failure regression added.
- Actual assignment exposed Hibernate orphan-delete collection replacement failure; changed aggregate-owned legs in place with defensive input copy, preserving existing domain assertions. Retained first failure. Reviewer requested stronger exact sequence and empty-candidate checks; implemented both and real rerouting per human mutation role.
- Final fresh run:63 Chromium assertions PASS,47 application checks PASS,35 domain cases PASS (one inherited empty TODO),seven mocked cleanup tests PASS. Exact selected/replacement voyages/locations/times and separate Reader readback, stale/invalid/forged/CSRF denials, role credentials and empty candidate case verified. No independent denied-write DB/queue/audit absence claim.
- App/browser/private network and three private realm/client files removed; historical app HTTP200, source clean and Jenkins preserved. KAN-15/KAN-18/KAN-19 remain In Progress; KAN-14 still502 BLOCKED. Independent review approved publication with no remaining material findings:253 hashes verified,63/47/35 records inspected,seven cleanup tests independently rerun; coverage/Javadoc notes resolved. Publication proceeds under standing authorization. Human effort/review time/cost unavailable; no savings claim.

## 1 November 2026 — Secured routing publication

- Standing user authorization applied after separate agent approval and passing checks. Verified253 reviewed input hashes and selected sanitized evidence; seven cleanup regressions pass. Included reviewed source/tests/docs, retained assignment failure and exact review record. No private realm/client credential files, raw logs or browser state included.
- No runtime redeployment/full CI rerun during publication. KAN-15/KAN-18/KAN-19 remain In Progress and KAN-14 remains502 BLOCKED for outstanding scope; earlier pending-publication snapshots are historical.

## 1 November 2026 — KAN-17 endpoint session security

Implemented authenticated/origin-allowlisted session-bound sockets, logout and HTTP-idle closure, and safe send failure isolation. Actual89 browser/47 application/35 domain PASS (one inherited empty TODO). Independent reviewer /root/review_kan17_socket approved code/docs/evidence, verified255 hashes; no remaining material findings. Map UI remains disabled; malformed/abrupt variants source-review only. Task runtime/network/private files removed; original services preserved. Published under standing authorization; full candidate/KAN-14 acceptance remains open. Human effort/cost unavailable.

## 1 November 2026 — KAN-19 live tracking UI

Restored authenticated live cargo plot/table with local assets, real inspection updates, marker/detail links, connection state and DOM clearing on logout/idle expiry. Preserved original socket name fields with added explicit codes; generation/abort/time ordering guards prevent stale snapshot replacement. Final107 browser/47 application/35 domain PASS (one inherited empty TODO); seven mocked cleanup regressions PASS. Actual all-role UI updates/marker movement, delayed snapshot, post-revocation empty views and authorized post-expiry event verified. Historical services/source preserved; task resources removed. Independent review/recheck approved publication with no remaining material findings;261 hashes verified and seven mocked cleanup tests independently rerun. Unique final NewYork event confirms post-expiry delivery. KAN-19 mobile logger remains open; KAN-14 independent absence still unverified. No savings/cost/time claims.

Publication: standing authorization applied after reviewer approval;261 staged reviewed hashes checked, no runtime redeployment/full CI rerun. KAN-19 continues with mobile logger; prior pending statements are historical.
