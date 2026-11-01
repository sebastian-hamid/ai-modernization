# Legacy baseline: functional documentation

Prepared 28 October 2026 against the pinned legacy source. **Current behavior**, not the approved target implementation. Source review was performed for this document; runtime statements refer to archived tests from 23–27 October, not a fresh browser walkthrough. See [verification method](README.md).

## Purpose, users and vocabulary

Cargo Tracker demonstrates cargo booking, routing and tracking across voyages and locations. Its interfaces serve booking staff, handling staff and people following cargo progress. These are functional personas, not enforced legacy security roles. There is no configured application login/role boundary in the verified baseline. The approved Reader/Operator/Administrator roles and authenticated tracking belong to the [modernization proposal](../../specifications/modernization-proposal.md), not this application today.

| Term | Meaning |
| --- | --- |
| Cargo / tracking ID | Shipment identity used to look up a booking and its history. An ID is not an authorization credential. |
| Route specification | Requested origin, destination and arrival deadline. |
| Itinerary / leg | Assigned journey, divided into legs with voyage, endpoints and times. |
| Voyage / carrier movement | Carrier schedule, divided into movements between locations. |
| Handling event | Recorded RECEIVE, LOAD, UNLOAD, CUSTOMS or CLAIM operation, with completion/registration dates and location. |
| Delivery | Derived snapshot of transport/routing state, last known location and next expected activity. |

Sources: [BookingService](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/application/BookingService.java), [Cargo](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/domain/model/cargo/Cargo.java), [RouteSpecification](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/domain/model/cargo/RouteSpecification.java), [Delivery](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/domain/model/cargo/Delivery.java).

## Workflows and verification

| ID | Workflow / user outcome | Preconditions and result | Evidence level |
| --- | --- | --- | --- |
| F01 | Book cargo | Choose known, distinct origin/destination and an arrival deadline. Application generates a tracking ID and stores unrouted, NOT_RECEIVED cargo. | Four-step booking integration suite verifies the service result. UI booking wizard completion is not yet tested. |
| F02 | Request routes and assign one | Use an existing booking. Route adapter requests candidates and filters them against origin/destination/deadline. Assignment stores an itinerary and updates delivery. | Booking integration tests; HTTP graph invariants. UI selection not exercised end to end. |
| F03 | Change destination | Existing cargo and known new destination; origin/deadline are retained. Delivery/routing is recalculated against the existing itinerary, which can become unsuitable. | Booking integration tests. Missing-ID UI requests produce known 500 errors. |
| F04 | Track cargo | Submit a tracking ID through the public JSF form; inspect status/history. Dashboard/details expose broader operational information. | Session-aware form submission for ABC123 and direct-page/API checks. Full client-side maps not verified. |
| F05 | Report handling | Supply valid report fields; factory requires known cargo/location and voyage where appropriate. Accepted REST input is queued, processed, stored and delivery re-evaluated asynchronously. | All five event types have live coverage across handling/entrypoint suites. |
| F06 | Follow live updates | Open tracking WebSocket; cargo-inspection events trigger JSON broadcasts. | Source reviewed; anonymous cross-origin upgrade verified. Actual message delivery and browser updates remain untested. |
| F07 | Log events from mobile UI | Enter the Faces flow through mobile.xhtml. Select event information and submit through its backing bean. | Source reviewed/redirect verified. Direct flow-view access returns 500; complete mobile workflow is unverified. |
| F08 | Import handling files | Scheduler runs the batch reader/writer over upload files, queues parsed attempts and writes archive/failed lines. | Source reviewed only; no end-to-end import/restart/permission test. |

Workflow sources: [DefaultBookingService](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/application/internal/DefaultBookingService.java), [ExternalRoutingService](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/infrastructure/routing/ExternalRoutingService.java), [EventBackingBean](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/interfaces/handling/mobile/EventBackingBean.java), [EventItemReader](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/interfaces/handling/file/EventItemReader.java), [EventItemWriter](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/interfaces/handling/file/EventItemWriter.java). Test evidence: [booking runtime notes](../../notes/legacy-runtime.md), [handling characterization](../../notes/handling-characterization.md), [coverage review](../../notes/test-coverage-review.md).

### Tracking lookup details (source-reviewed)

Demo seed IDs such as ABC123 are fixed examples. Newly booked IDs are generated from the first eight uppercase characters of a random UUID; do not describe all issued IDs as sequential or predictably generated. Neither form is an access credential. Track trims entered IDs, loads the matching cargo/history and adds a not-found message when lookup returns null; malformed/empty input and the complete browser error path are not newly verified here. Its autocomplete method returns all tracking IDs without filtering by the supplied query, another data-exposure consideration for future access controls.

Sources: [JpaCargoRepository](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/infrastructure/persistence/jpa/JpaCargoRepository.java), [Track](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/interfaces/tracking/web/Track.java).

## Business rules and state

- Origin, destination and deadline must be present; origin and destination must differ. A route satisfies its specification when endpoints match and final arrival is **strictly before** the deadline. Do not infer universal strict date parsing from this domain rule: REST uses lenient date parsing.
- LOAD and UNLOAD require a voyage. RECEIVE, CUSTOMS and CLAIM prohibit a supplied voyage. A known voyage is looked up before an event is created. The factory's null-result contract differs from the real JPA lookup behavior for unknown locations/voyages.
- Latest completion time, rather than submission order, selects the most recent handling event. Completion dates persist with DATE precision; same-day ties and concurrent updates are not fully characterized.
- Transport states are NOT_RECEIVED, IN_PORT, ONBOARD_CARRIER, CLAIMED and UNKNOWN. Routing states are NOT_ROUTED, ROUTED and MISROUTED. Misdirection is a separate flag comparing handling against the itinerary.
- `atDestination` reflects the latest UNLOAD at the destination. It is not a permanent delivered flag: the recorded route test sets it true on final UNLOAD and false after CLAIM.

A normal routed journey is RECEIVE at origin → LOAD → UNLOAD (repeat for transfers) → final UNLOAD → CLAIM. CUSTOMS is an additional event type. This sequence describes the successful test journey, not a fully enforced state machine: the baseline accepts an off-route LOAD after CLAIM and marks cargo misdirected.

Sources: [RouteSpecification](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/domain/model/cargo/RouteSpecification.java), [HandlingEvent](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/domain/model/handling/HandlingEvent.java), [HandlingEventFactory](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/domain/model/handling/HandlingEventFactory.java), [HandlingHistory](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/domain/model/handling/HandlingHistory.java), [Delivery](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/domain/model/cargo/Delivery.java).

## Input and error behavior

REST handling reports use completionTime (`yyyy-MM-dd HH:mm`), trackingId, eventType, unLocode and optional voyageNumber. Required fields and length constraints are detailed in [technical documentation](technical.md). Recorded outcomes:

| Scenario | Legacy outcome |
| --- | --- |
| Missing/null/empty/short required values, invalid constrained lengths | HTTP 400 in tested cases. |
| Unsupported report media type | HTTP 415. |
| Unknown enum, lowercase enum, unparsable time or invalid location syntax | Tested examples return 500. |
| Invalid calendar date of valid length | February 30 accepted by lenient parsing. |
| Unknown cargo/location/voyage or missing/prohibited voyage | HTTP 204 can be followed by asynchronous processing failure. |
| Unknown/missing cargo on some direct admin links | HTTP 500 rather than a controlled not-found response. |
| Anonymous operational access | Data reads and a verified state-changing report succeed; desired security gate fails. |

A 204 is **not proof of successful registration**. Negative tests require fresh failure logs plus bounded unchanged-state observations; final retry/dead-letter disposition remains unverified. Sources: [HandlingReportService](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/interfaces/handling/rest/HandlingReportService.java), [HandlingReport](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/interfaces/handling/rest/HandlingReport.java); [recorded access/input findings](../../notes/test-coverage-review.md).

## Demonstration data and limitations

Seeds include ABC123, JKL567, DEF789 and MNO456, with historical 2016 journeys. The sample initializer deletes existing application records before reloading them. Never interpret this baseline as durable business storage. Route simulation uses current/random dates, which interact with historical deadlines; exact candidate lists are not stable.

Known gaps include full browser workflows, role/session/ownership behavior, CSV execution, replay/concurrency, final messaging failure disposition and resilient restarts. Those gaps are not successful or implicitly supported behavior. Sources: [SampleDataGenerator](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/cargotracker/application/util/SampleDataGenerator.java), [GraphTraversalService](https://github.com/javaee/cargotracker/blob/57fc7b32d2597e43b5e0d454e707e0146de5258a/src/main/java/net/java/pathfinder/api/GraphTraversalService.java); [coverage matrix](../../notes/test-coverage-review.md).
