# Candidate API access matrix (KAN-15)

## Functional scope

The fresh live subset covers all 27 definitions for the three HTTP APIs, including their human session cases and the scoped routing identity. Together with eight private-template definitions and 20 private metadata/source-note definitions this is 55 bound definitions; the other 447 catalogue definitions remain unsupported/BLOCKED and the full gate must exit 2.

| API | Anonymous | Reader | Operator / Administrator | Revoked session |
| --- | --- | --- | --- | --- |
| Cargo monitoring GET/HEAD |401, no fixture cargo markers |Actual seeded JSON on GET; 200 empty-body HEAD |Same read semantics |All three human roles: GET/HEAD 401, empty HEAD body |
| Handling POST |401, independent effects unchanged |403, independent effects unchanged |204 acceptance followed by actual asynchronous persisted effect |Operator/Administrator:401 and independent effects unchanged |
| Graph routing GET |401, no route payload |403, no route payload |Actual nonempty connected route candidates |Operator/Administrator:401, no route payload |
| Native routing service GET |Separate scoped credential only |Human Basic cannot impersonate it |Human role access is independently tested |Basic request returns no reusable authenticated session |

The test parser supports the pinned JSON-B Date representation with its observed [UTC] suffix, requires a matching zero offset, and rejects other/malformed region suffixes. An initially stricter Python parser rejected this legitimate format; corrected with exact-format and invalid-region regressions, without changing the planner.

Route semantics require the requested CNHKG origin and FIHEL destination, connected intermediate legs, nonempty voyage fields and valid timezone-aware ordered departure/arrival timestamps. This validates the existing sample planner's response, not real timetable optimization or deadline filtering.

Allowed handling is not accepted on 204 alone. Operator and Administrator each produce a changed cargo in a separate Reader readback, changed SQL content hashes, increased cumulative broker counts and a handling business invocation. Operator's positive control also explicitly proves both expected MDB onMessage observers are connected. Admin's distinct cargo/event ensures its readback does not pass because of the Operator write.

## Session and denial evidence

For every human role, the fixture authenticates a native principal/role, performs an actual permitted monitoring request, saves cookie/token privately and then logs out. After server identity revocation is verified, saved credentials replay the relevant APIs. Separate fresh sessions for all three roles are then left without HTTP traffic for at least 75 seconds after the last login in the one-minute-timeout lab, and the same replays are checked.

Each per-role logout/expiry cohort is enclosed by settled independent SQL/broker/invocation snapshots. Read denials and permitted-to-write role POST replays all occur inside that window. Anonymous/Reader handling and CSRF/forged-booking denials retain their existing shared cohort. Counter/hash equality is bounded observed absence, not exhaustive proof against arbitrarily delayed effects. Complete denied-write acceptance remains false.

## Scoped routing identity

A lab-only RoutingIdentityFilter records the actual HttpServletRequest principal and role answers after the explicit native authentication/access filters. A local MBean exposes that record to the existing local-attach observer; no HTTP observer or host/JMX port is added. It never reads/stores Authorization, passwords, cookies or tokens.

The test observes a sequence value, executes one Basic request, and requires exactly one new record: principal routing, RoutingService role, no Reader/Operator/Administrator roles, and the fixed graph endpoint path. This is exact among the declared application roles; it does not enumerate arbitrary undeclared server roles. The fixture realm file assigns routing only RoutingService. Route semantics and existing wrong-password/human-impersonation/malformed-header/out-of-scope-monitoring/no-reusable-Basic-session checks must pass before the machine observation is bound.

The approved inventory's descriptive required_machine_scope is mapped to this observed native RoutingService capability. It is never accepted from an HTTP client claim. This does not establish broker, filesystem, deployment or migration authority, and does not claim service credentials cannot be supplied to the form-login servlet. Scope remains restricted by server roles regardless of how credentials are supplied.

## Adapter and technical verification

The adapter constructs canonical cases from the approved inventory but only binds explicitly supported fixed paths/methods. A supplied case must equal its full canonical contract, including actor, state, source and machine scope. Missing observations remain unsupported. Changing a case's ID alone, path, actor, method, session metadata or required scope cannot reuse an observation.

Run from WSL repository root:

    python3 tests/security/run_candidate_contracts.py --live-subset
    python3 tests/browser-workflows/run_browser.py
    python3 -m unittest discover -s tests/security -p 'test_*.py' -v
    python3 -m unittest discover -s tests/candidate-runtime -p 'test_*.py' -v

Final exact inputs and sanitized evidence are under notes/evidence/kan-15-api-matrix; independent review is separate. Earlier 4 PASS / 16 PASS records remain historical. No production application-source or permission change is included: instrumentation is overlaid only into the opt-in disposable image. The historical app/Jenkins and read-only sources are preserved. H2/Chromium and inherited empty-domain-test limits remain; full UI/actions/internal workers/imports/retry/restart/platform acceptance is separate.


## Private metadata and source notes

All four actors also request the five inventoried private URLs: faces-config.xml, glassfish-web.xml, web.xml, weblogic.xml under WEB-INF, and booking/todo.txt. Each must return 404 without fixture cargo markers, configuration root elements or application source package text. Native role identity is checked for human-role requests.

The actual built WAR entry list records whether each resource is packaged. A 404 for an omitted resource proves unavailability, not that an existing file was guarded; the packaging flags keep that distinction visible. Existing packaged descriptors/source notes provide the relevant direct-access negative controls. These twenty definitions are separate from the eight private-template definitions. Resource name normalization/encoding bypass variants remain future scenarios.

An earlier browser regression preceded the private-resource extension by 20 GET checks. Its image was no longer locally available for artifact comparison, so exact old/new artifact identity was not claimed. A fresh current regression subsequently passed all 156 application checks and 210 browser assertions, including the private-resource extension. Reports retain each run's actual application count and image ID.
