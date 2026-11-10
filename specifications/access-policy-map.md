# KAN-12: entrypoint and action access-policy map

Prepared 1 November 2026. [Jira KAN-12](https://ai-modernization.atlassian.net/browse/KAN-12). Source: unchanged Cargo Tracker commit `57fc7b32d2597e43b5e0d454e707e0146de5258a`. **Desired-policy design and source inventory, not implemented security or passing access tests.** Baseline security findings remain open.

This applies the [approved proposal](modernization-proposal.md): Reader can read cargo/tracking/dashboard/live data; Operator adds booking/routing/destination changes/handling reports; Administrator adds controlled imports/batch. All cargo information and operational functions require authentication. Landing, public About, login and necessary safe static resources are the only public content. Roles are explicitly mapped; do not assume name-based inheritance. Shared organizational cargo visibility is approved; customer/tenant isolation is not implemented or claimed.

## Deliverables and reproducibility

- [Machine-readable inventory](access-policy-inventory.json): exact paths, active view bindings/source lines, permissions, enforcement boundaries, logical test locations, annotation census and source hashes.
- [Generator](../scripts/build-access-inventory.py): pinned-source inventory with no network/runtime calls; refuses a changed checkout or unclassified page.
- [Validation evidence](../notes/evidence/kan-12-access-map/validation.json): file census, policy invariants, regeneration determinism and source identity.

Run from repository root: `python3 scripts/build-access-inventory.py`. Generated output is deterministic for the pinned source. Preserve the historical checkout and treat synced sources as read-only. A new page, API or callback requires explicit classification; this static inventory is not a proof of runtime reachability or complete reflection/dynamic-route discovery.

## Enforcement and test conventions

| Code | Required enforcement boundary |
| --- | --- |
| E1 | Server/container HTTP authorization before Faces rendering, getters, view actions, parameter binding or repository calls. Exact exceptions to protected path groups; no public wildcard for /public/ or /admin/. |
| E2 | Backing actions and business-service operations independently enforce allowed roles before database writes, route assignment or JMS submission. Hidden/disabled controls and valid view state do not grant permission. |
| E3 | GET/HEAD REST guards plus repository read boundary; unauthorized calls never receive cargo JSON or HTML login with a success status. |
| E4 | Authenticated POST guard, role/CSRF checks where cookie sessions are used, then input validation and trusted event producer. No queue message on denied input. |
| E5 | WebSocket authentication/role/origin checks before 101; authorize actual broadcasts and invalidate session-bound access at logout/expiry. |
| E6 | Separate internal HTTP, worker, broker, filesystem, scheduler and deployment authority. Application roles do not grant Jenkins/server/database administration. |
| E7 | Deny private templates/config/source notes; explicitly allow reviewed non-sensitive static files. Dynamic resource/AJAX dispatch must not execute unguarded application behavior. |

Test locations below are **logical candidate suites to implement in KAN-14**, not existing executable tests. Browser/service/API framework choices remain open. Every row has test groups in the JSON; groups are detailed later in this document.

## Page and template matrix

All paths are under `/cargo-tracker`. `R/O/A` means Reader, Operator and Administrator; `O/A` means Operator and Administrator. Denied means no human role may request the raw resource directly; application includes still execute under the original caller's authorization.

| ID | Exact page path | Anonymous | Roles | Enforcement | Required checks |
| --- | --- | --- | --- | --- | --- |
| PAGE-01 | `/WEB-INF/templates/common/admin.xhtml` | Deny | None (direct access denied) | E7 | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-02 | `/WEB-INF/templates/common/public.xhtml` | Deny | None (direct access denied) | E7 | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-03 | `/admin/about.xhtml` | Deny | R/O/A | E1 + read boundary | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-04 | `/admin/changeDestination.xhtml` | Deny | O/A | E1 + E2 | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-05 | `/admin/dashboard.xhtml` | Deny | R/O/A | E1 + read boundary | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-06 | `/admin/listClaimed.xhtml` | Deny | R/O/A | E1 + read boundary | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-07 | `/admin/listNotRouted.xhtml` | Deny | R/O/A | E1 + read boundary | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-08 | `/admin/listRouted.xhtml` | Deny | R/O/A | E1 + read boundary | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-09 | `/admin/map.xhtml` | Deny | R/O/A | E1 + read boundary | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-10 | `/admin/mapFrame.html` | Deny | R/O/A | E1 + read boundary | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-11 | `/admin/route.xhtml` | Deny | O/A | E1 + E2 | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-12 | `/admin/selectItinerary.xhtml` | Deny | O/A | E1 + E2 | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-13 | `/admin/show.xhtml` | Deny | R/O/A | E1 + read boundary | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-14 | `/admin/track.xhtml` | Deny | R/O/A | E1 + read boundary | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-15 | `/booking/booking-date.xhtml` | Deny | O/A | E1 + E2 | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-16 | `/booking/booking-destination.xhtml` | Deny | O/A | E1 + E2 | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-17 | `/booking/booking.xhtml` | Deny | O/A | E1 + E2 | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-18 | `/error.xhtml` | Allow sanitized content | R/O/A | E1/E7 | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-19 | `/error_404.xhtml` | Allow sanitized content | R/O/A | E1/E7 | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-20 | `/eventLogger/eventLogger.xhtml` | Deny | O/A | E1 + E2 | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-21 | `/eventLogger/root.xhtml` | Deny | O/A | E1 + E2 | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-22 | `/index.xhtml` | Allow sanitized content | R/O/A | E1/E7 | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-23 | `/mobile.xhtml` | Deny | O/A | E1 + E2 | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-24 | `/public/about.xhtml` | Allow sanitized content | R/O/A | E1/E7 | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |
| PAGE-25 | `/public/track.xhtml` | Deny | R/O/A | E1 + read boundary | PAGE-DIRECT, RENDER-NO-LEAK; AJAX/flow cases where applicable |

Important cases:

- `/public/track.xhtml` is protected despite its legacy folder name. `/public/about.xhtml` is the public About page. `/admin/about.xhtml` remains a read-only operational view using the admin layout; do not automatically expose all admin URLs because one is called About.
- `/admin/mapFrame.html` is a separate direct-request target, not only an iframe. It fetches `/rest/cargo` and opens `/tracking`; protect all three and update HTTP/ws transport assumptions for HTTPS in the candidate.
- Dashboard/list views mix Reader-visible data with Operator-only navigation and mutation controls. Render authorized controls appropriately; separately reject Reader POST/AJAX/action replay and service invocation. A protected dialog URL is not enough.
- Direct booking/eventLogger view access, cached view state and flow-return replay require the same checks as normal navigation. `booking-flow.xml`/`eventLogger-flow.xml` are internal metadata, not public APIs; deny raw XML requests for every role.
- `error.xhtml` and `error_404.xhtml` may expose only generic sanitized responses. Do not return operational details on error/forward/include dispatch, failed authorization or malformed IDs.
- No login/logout endpoint exists in the pinned source. Target login/session/logout and form-processing routes must be explicitly mapped during implementation; no path is invented here. Logout/session expiry invalidates authorization, including long-lived views/sockets.

## Active JSF actions, callbacks and navigation

The generator strips XML comments and records all active action/actionListener/listener/completeMethod/outcome/onclick/onload occurrences relevant to navigation or EL. Duplicate uses are separate occurrences because page/role context differs. Managed property getters and setters are also covered by the E1 rendering boundary and service-read rules; this callback list is not an exhaustive list of every EL property evaluation.

| ID | View/source line | Callback/navigation expression | Roles at invocation | Mutation |
| --- | --- | --- | --- | --- |
| ACTION-01 | `WEB-INF/templates/common/admin.xhtml:29` | `/admin/dashboard.xhtml` | R/O/A | No domain write identified; guard data/flow before execution |
| ACTION-02 | `WEB-INF/templates/common/admin.xhtml:31` | `booking` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-03 | `WEB-INF/templates/common/admin.xhtml:33` | `/admin/track.xhtml` | R/O/A | No domain write identified; guard data/flow before execution |
| ACTION-04 | `WEB-INF/templates/common/admin.xhtml:35` | `/admin/map.xhtml` | R/O/A | No domain write identified; guard data/flow before execution |
| ACTION-05 | `WEB-INF/templates/common/admin.xhtml:37` | `/admin/about.xhtml` | R/O/A | No domain write identified; guard data/flow before execution |
| ACTION-06 | `WEB-INF/templates/common/public.xhtml:29` | `/public/about.xhtml` | R/O/A; public navigation allowed | No domain write identified; guard data/flow before execution |
| ACTION-07 | `admin/changeDestination.xhtml:13` | `#{changeDestination.load}` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-08 | `admin/changeDestination.xhtml:39` | `#{changeDestinationDialog.cancel()}` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-09 | `admin/changeDestination.xhtml:43` | `#{changeDestination.changeDestination()}` | O/A | Yes — E2/E4, DENIED-NO-SIDE-EFFECT |
| ACTION-10 | `admin/listClaimed.xhtml:10` | `show.xhtml?faces-redirect=true` | R/O/A | No domain write identified; guard data/flow before execution |
| ACTION-11 | `admin/listNotRouted.xhtml:10` | `route.xhtml?faces-redirect=true` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-12 | `admin/listNotRouted.xhtml:23` | `#{changeDestinationDialog.showDialog(cargoNotRouted.trackingId)}` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-13 | `admin/listNotRouted.xhtml:27` | `#{changeDestinationDialog.handleReturn}` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-14 | `admin/listRouted.xhtml:10` | `show.xhtml?faces-redirect=true` | R/O/A | No domain write identified; guard data/flow before execution |
| ACTION-15 | `admin/route.xhtml:13` | `#{cargoDetails.load}` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-16 | `admin/route.xhtml:15` | `#{itinerarySelection.load}` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-17 | `admin/route.xhtml:53` | `#{itinerarySelection.assignItinerary(itineraryStatus.index)}` | O/A | Yes — E2/E4, DENIED-NO-SIDE-EFFECT |
| ACTION-18 | `admin/selectItinerary.xhtml:11` | `#{itinerarySelection.load}` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-19 | `admin/selectItinerary.xhtml:60` | `#{itinerarySelection.assignItinerary(itineraryStatus.index)}` | O/A | Yes — E2/E4, DENIED-NO-SIDE-EFFECT |
| ACTION-20 | `admin/show.xhtml:22` | `#{cargoDetails.load()}` | R/O/A | No domain write identified; guard data/flow before execution |
| ACTION-21 | `admin/show.xhtml:63` | `selectItinerary.xhtml?faces-redirect=true` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-22 | `admin/show.xhtml:107` | `selectItinerary.xhtml?faces-redirect=true` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-23 | `admin/track.xhtml:19` | `#{track.completeTracking}` | R/O/A | No domain write identified; guard data/flow before execution |
| ACTION-24 | `admin/track.xhtml:20` | `#{track.onTrackById}` | R/O/A | No domain write identified; guard data/flow before execution |
| ACTION-25 | `admin/track.xhtml:60` | `#{track.onPointSelect}` | R/O/A | No domain write identified; guard data/flow before execution |
| ACTION-26 | `booking/booking-date.xhtml:33` | `#{bookingBackingBean.deadlineUpdated}` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-27 | `booking/booking-date.xhtml:46` | `booking-destination` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-28 | `booking/booking-date.xhtml:47` | `/admin/dashboard` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-29 | `booking/booking-date.xhtml:48` | `#{bookingBackingBean.register()}` | O/A | Yes — E2/E4, DENIED-NO-SIDE-EFFECT |
| ACTION-30 | `booking/booking-destination.xhtml:38` | `booking` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-31 | `booking/booking-destination.xhtml:39` | `/admin/dashboard` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-32 | `booking/booking-destination.xhtml:40` | `booking-date` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-33 | `booking/booking.xhtml:36` | `/admin/dashboard` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-34 | `booking/booking.xhtml:36` | `booking-destination` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-35 | `eventLogger/eventLogger.xhtml:24` | `pm:secondScreen?transition=flip` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-36 | `eventLogger/eventLogger.xhtml:38` | `#{eventBackingBean.updateVoyage}` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-37 | `eventLogger/eventLogger.xhtml:47` | `#{eventBackingBean.updateListener}` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-38 | `eventLogger/eventLogger.xhtml:61` | `#{eventBackingBean.updateListenerEvent}` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-39 | `eventLogger/eventLogger.xhtml:68` | `#{eventBackingBean.updateListenerEvent}` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-40 | `eventLogger/eventLogger.xhtml:86` | `pm:firstScreen?transition=flip` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-41 | `eventLogger/eventLogger.xhtml:90` | `#{eventBackingBean.handleEventSubmission}` | O/A | Yes — E2/E4, DENIED-NO-SIDE-EFFECT |
| ACTION-42 | `eventLogger/eventLogger.xhtml:107` | `#{eventBackingBean.timeSet()}` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-43 | `mobile.xhtml:10` | `#{holderBean.initFlow}` | O/A | No domain write identified; guard data/flow before execution |
| ACTION-44 | `public/track.xhtml:17` | `#{track.getTrackingIds}` | R/O/A | No domain write identified; guard data/flow before execution |
| ACTION-45 | `public/track.xhtml:18` | `#{track.onTrackById}` | R/O/A | No domain write identified; guard data/flow before execution |

Navigation invocation must satisfy both the source-view context and destination policy; relative links to route/itinerary selection remain O/A even on Reader-visible views. Internal-template navigation inherits the target permission without allowing direct template requests.

Every callback requires JSF-AJAX, DIRECT-REPLAY and SESSION-EXPIRED cases; actual writes additionally require DENIED-NO-SIDE-EFFECT and CSRF cases. `itinerarySelection.load` performs internal route retrieval on GET/view action, so protect before execution, not only on assign.

Unresolved legacy bindings are inventory findings, not invented working methods: `track.completeTracking` and `track.onPointSelect` are referenced by admin/track but absent from the Track class; flow-return expressions reference `bookingBean.returnValue` while the inspected booking bean is named bookingBackingBean. Existing rendering defects stay in KAN-20; compatibility work must resolve or prove bindings before asserting happy-path coverage.

Alternate managed-bean paths also require E2: `Registration.register` and `CargoAdmin.register/assignItinerary/changeDestination` exist even where no active page binding was found in this census. `BookingService.bookNewCargo/assignCargoToRoute/changeDestination` and booking facade mutations allow O/A; route-candidate retrieval allows O/A because it calls the protected simulator. Read-only cargo/history/location operations allow R/O/A from authorized adapters; repository interfaces are not public HTTP endpoints.

## REST, WebSocket and internal routing

| ID | Interface / entry method | Allowed human roles | Enforcement / logical candidate test suite |
| --- | --- | --- | --- |
| API-01 | `GET/HEAD /cargo-tracker/rest/cargo` — `CargoMonitoringService.getAllCargo` | R/O/A; anonymous denied | E3/E6 / API and internal-caller policy |
| API-02 | `POST /cargo-tracker/rest/handling/reports` — `HandlingReportService.submitReport` | O/A; anonymous denied | E4 / API write policy |
| API-03 | `GET /cargo-tracker/rest/graph-traversal/shortest-path` — `GraphTraversalService.findShortestPath` | O/A; anonymous denied | E3/E6 / API and internal-caller policy |
| WS-01 | `HTTP Upgrade / send / close /cargo-tracker/tracking` — `RealtimeCargoTrackingService.onOpen/onCargoInspected/onClose` | R/O/A; anonymous denied | E5 / WebSocket policy |

For APIs: unauthenticated requests produce 401 and authenticated insufficient-role requests produce 403; no 200 login HTML or misleading 204. Authenticate before cargo lookup, report parsing side effects or source exception leakage. Valid denied inputs must be checked, not only malformed JSON. Unsupported methods cannot bypass permissions; return controlled 405 where appropriate without executing resource methods. OPTIONS/CORS behavior must be designed explicitly rather than exempting every operational request. Same-origin JSF AJAX and cross-origin browser requests need separate checks.

**Routing machine caller:** ExternalRoutingService calls the graph endpoint from inside the WAR. Protecting only the endpoint without supplying trusted caller authority would break booking. The map requires a narrow routing capability/dedicated service identity and explicitly denies broad interactive privileges to that identity. Exact WildFly credential propagation and mapping are an implementation choice to verify in KAN-13/KAN-15; no new human role is introduced here. Reject forged identity headers, payload role claims and unrelated service-identity calls to handling/admin endpoints. The internal caller must still enforce the initiating O/A action.

**WebSocket:** authenticate upgrade and allowed origin, then test actual allowed/denied messages and logout/expiry, not handshake only. Browser WebSocket authentication may use the approved session; it must not send passwords in a URL. Existing unrelated-Origin/anonymous 101 evidence is a baseline failure of the desired policy, not a target contract. No customer-specific per-cargo filtering is claimed under the approved shared-organizational visibility.

## Batch, files, messaging and startup

| ID | Entry boundary | Approved control / enforcement | Logical candidate suite |
| --- | --- | --- | --- |
| BG-01 | `UploadDirectoryScanner.processFiles -> EventFilesProcessorJob` | Administrator controls enablement/trigger; disabled in candidate until controlled invocation is implemented. Trusted scheduler/batch worker; no implied logged-in human principal. E6. | BATCH-TRIGGER, BATCH-FS, DENIED-NO-SIDE-EFFECT |
| BG-02 | `/tmp/uploads -> EventItemReader -> EventItemWriter; /tmp/archive and /tmp/failed` | Administrator-controlled ingestion; OS/container filesystem ACLs restrict upload/archive/failed paths to dedicated worker and approved administration tooling. Trusted filesystem producer and batch worker, not untrusted HTTP caller. E6. | BATCH-FS, BATCH-REPLAY, LEAST-PRIVILEGE |
| BG-03 | `HandlingEventRegistrationAttemptQueue -> HandlingEventRegistrationAttemptConsumer` | Only authorized operator/admin submission adapters and trusted batch worker may enqueue; broker/JNDI access restricts arbitrary producers. Dedicated server worker authority; human identity does not automatically propagate through ObjectMessage. E6. | JMS-PRODUCER, DENIED-NO-SIDE-EFFECT, BATCH-REPLAY |
| BG-04 | `CargoHandledQueue -> CargoHandledConsumer -> inspectCargo -> CargoInspected` | Trusted registration-service producer and inspection worker; no public direct invocation. Server worker; audit origin/correlation to be designed, not trusted role fields in payload. E6. | JMS-PRODUCER, WS-DATA, LEAST-PRIVILEGE |
| BG-05 | `DeliveredCargoQueue / MisdirectedCargoQueue / RejectedRegistrationAttemptsQueue consumers` | Trusted producer/consumer bindings and sanitized restricted logs; rejection producer/final disposition still unverified. Server workers. E6. | JMS-PRODUCER, LOG-NO-LEAK |
| BG-06 | `SampleDataGenerator.loadSampleData and ORM startup schema creation` | Disable destructive reseeding/schema creation in deployed candidate; controlled installation/migration process only. Deployment/migration identity separate from request users. E6. | STARTUP-NO-DELETE, LEAST-PRIVILEGE |

Administrator may initiate/enable the approved controlled batch/import feature; a scheduler/MDB does not become an Administrator merely because it runs in the server. No request login is inherited by ObjectMessage consumption. Restrict producers and broker lookup, establish a trusted worker execution context and preserve origin/correlation for audit. Choose worker/run-as configuration deliberately during implementation; do not trust role strings embedded in import files or message bodies. No raw queue/admin listener should be published to make this work.

Filesystem permission checks use OS/container identities, not application role names. Operators/Readers/anonymous clients cannot write import directories via an alternate upload path. Check symlinks/path traversal, unfiltered directory entries, archive/failed file privacy and replay. A new upload/trigger API would need an explicit route and permission; none exists in this source. Candidate scheduled scanning remains disabled until the controlled trigger/worker path is implemented and tested.

Startup data deletion and schema creation are installation/deployment concerns; neither Administrator nor any other application role gains database/Jenkins/server administration rights. Disable demo reseeding/schema creation in deployed candidate environments and use the separately approved migration identity/Flyway process. Preserve legacy behavior only in the historical disposable baseline.

For BG-06 acceptance, the machine allow case covers Flyway schema migration only, using the server-verified schema_migrator identity. It does not authorize SampleDataGenerator, demo seeding, reseeding, or ORM-driven DDL. The candidate's Administrator handling-event import UI at /admin/import.xhtml is a separate BG-01/BG-02 capability: it runs through the BatchTrigger/BatchWorker boundary and must not be interpreted as permission to seed demo data or alter schema. The four human BG-06 cases cover denial of any user-triggerable startup/reseed/schema-action surface; an absent surface must be established by a complete exposure inventory and direct probes, not by a guessed 404 alone. The existing /admin/import.xhtml path is the candidate control-plane implementation for the legacy BG-01/BG-02 handling-event import entries; verify its authorization and effects under those cases. Any additional import capability beyond that route needs separate approval and tests, and does not grant database or schema administration.

## Static, metadata, aliases and default deny

The inventory lists 41 resource/image candidates and all private auxiliary files. Whitelist only reviewed assets needed for public/login rendering; no user/cargo data or credentials in static responses. Keep JSF library resources distinct from dynamic bean requests. Deny WEB-INF/META-INF, flow XML metadata, `booking/todo.txt`, source files, config and unsupported mappings.

The pinned descriptor maps Faces only to `*.xhtml`; navigational strings include `show.html`, which is not proof of a deployed HTML alias. Test unregistered `.html`, welcome/trailing-slash, encoded/normalized paths, duplicate query parameters, direct fragments, forwards/includes/error dispatch and JSF resource/AJAX variations. Actual deployment mappings decide the reachable set; any new mapping requires inventory review. A wildcard `/public/*` permit or resource-handler exception must not reopen tracking/autocomplete/data methods.

## Desired test catalogue (design only)

Each matrix row maps to one or more test groups below. KAN-14 implements executable cases; KAN-15 implements enforcement. The generator validates inventory coverage, not security efficacy.

| Group | Logical test location and expected result |
| --- | --- |
| PAGE-DIRECT / RENDER-NO-LEAK | Candidate HTTP/browser suite: direct GET and relevant HEAD/POST for every page, with anonymous/R/O/A. Anonymous protected GET may redirect only to login; authenticated wrong role is denied; no cargo data, bean invocation or exception leakage before authorization. Public pages remain functional. |
| JSF-AJAX / DIRECT-REPLAY / FLOW-BYPASS | Candidate browser/action suite: real allowed submissions, crafted AJAX/partial requests, copied or stale view state, direct dialog/fragment/flow links, read getters and setter parameters. Revalidate caller roles on every request, independent of button visibility. |
| API-READ / API-WRITE / NO-LOGIN-HTML | Candidate API suite: valid identities/inputs for happy paths, anonymous/wrong-role/missing or invalid credentials, methods/content negotiation and malformed body. Check statuses, media types and absence of operational payload in denials. |
| DENIED-NO-SIDE-EFFECT | Candidate application/integration suite: compare database/event history before/after denied calls, spy/audit producer invocation and inspect queue/enqueue evidence; no accepted message or business mutation, including after async workers settle. A 403 alone or short unchanged monitor interval is insufficient proof. |
| CSRF / SESSION-EXPIRED | Candidate session/browser suite: missing/invalid CSRF token for cookie-backed writes, logout, timeout and saved page/dialog replay; no mutation. Valid token/authenticated permitted role succeeds. Do not store credentials in source or evidence. |
| INTERNAL-CALLER / LEAST-PRIVILEGE | Candidate internal/service suite: valid O/A booking traverses the protected route adapter; scoped service identity cannot invoke unrelated business/admin functions; forged headers/role payloads and anonymous direct EJB/service exposure fail. Explicit role mappings preserve R/O/A policy. |
| WS-UPGRADE / WS-ORIGIN / WS-DATA / WS-DISCONNECT | Candidate socket/browser suite: reject anonymous/wrong origin before 101; verify actual allowed frames, session expiration/logout revocation and safe abrupt disconnect with continued cargo processing. |
| BATCH-TRIGGER / BATCH-FS / BATCH-REPLAY | Candidate batch/filesystem suite: Administrator-controlled import succeeds through trusted worker; other roles/untrusted OS users cannot trigger/write; malicious paths/entries and replay do not bypass controls; audit/archives stay restricted. Test timers without assuming an interactive session. |
| JMS-PRODUCER / LOG-NO-LEAK | Candidate messaging suite: reject unauthorized producers/direct consumer triggers; valid worker path processes once according to agreed semantics; original identity/correlation is auditable; no secret/unauthorized payload in logs. Final retry/rejection semantics remain later resilience work. |
| STATIC-ALLOWLIST / RESOURCE-BYPASS | Candidate resource/HTTP suite: permitted assets render login/public pages; raw configs/templates/flow metadata/notes and encoded/alternate dispatch paths remain inaccessible; resource handlers do not invoke data getters anonymously. |
| STARTUP-NO-DELETE | Candidate deployment suite: restart preserves records; only dedicated migration tooling changes schema. Application roles/worker identities cannot acquire installation/database privileges. |

## Open implementation details and scope limits

This inventory derives human roles from the approved policy and introduces no broader grants. Exact internal credentials, worker identity/run-as, authentication/session timeout values, permitted deployment origins, CSRF and interceptor configuration, login/logout paths and executable test framework must be designed/verified with the candidate runtime. Any choice that changes the approved policy returns to the user. Operational `/admin/about.xhtml` stays protected; public About is available at `/public/about.xhtml`.

No live security tests, candidate deployment or historical source modifications occurred. Static scan ignores XML-commented actions and inventories explicit annotations/bindings; it does not prove arbitrary reflective calls or dependency-provided resource routes are safe. Review the final deployed route/resource handlers during KAN-14/KAN-15. Confirmed defects stay open in KAN-16/17/20/24/26 and related coverage tasks. No claim of fixed anonymous access, completed role tests or production readiness is made.
