# Proposal: current-UI acceptance with legacy traceability

**Status: proposed; user approval required before changing acceptance definitions or gate treatment.**

## Decision and recommendation

Use current user capabilities as the candidate's acceptance basis, retaining the complete legacy inventory as an audit/traceability record. Do not restore retired Faces dialog/wizard/mobile helper callbacks solely to make the old implementation census green. This changes acceptance/reporting treatment, so it needs an explicit user decision; existing modernization approval is not assumed to approve retiring individual test requirements.

The approved UI modernization replaced some framework-specific controls. The remaining 33 read-only callback definitions represent 132 active actor cases: 14 behaviors have current navigation/load equivalents; 19 helper/transition definitions are tied to retired widgets or flows. Treating those old callbacks as literally executed would be inaccurate. Leaving them permanently BLOCKED also conflates an obsolete implementation hook with a missing current user capability.

## Proposed treatment

1. Preserve all 502 original desired-case definitions and historical results. Keep modern mappings and their actual evidence explicit; never claim retired code executed.
2. Define a versioned current-capability gate with native identity, anonymous/role/session checks, direct/forged requests, no-leak inspection and independent denied-write effects. Existing validated evidence may support a mapping only when the exact capability and required controls match; a green aggregate report is insufficient.
3. Mark a legacy implementation-only definition RETIRED only after its replacement capability tests and retired-entry denial/alias tests pass and independent review verifies the mapping. RETIRED is not PASS and must not inflate the pass count or be silently removed from history.
4. Keep the 14 current-equivalent behaviors below pending until their specific drivers pass. Keep all unsupported worker/service/machine boundaries blocked. This proposal does not accept the remaining internal/worker gaps or declare full security acceptance.
5. Preserve approved roles, public/private boundaries, CSRF, revocation, business rules and side-effect requirements. Retired mutation POSTs must remain denied (including authenticated/CSRF-valid replay); legacy GET aliases require fixed local targets, authorization before lookup and safe invalid-input behavior.
6. Report current-gate coverage separately from the old 502-case audit. Publish explicit mapping and retired counts; do not present a changed denominator as newly passing execution.

## Current-equivalent behaviors: keep required

These are proposed driver targets, not claims that all are already tested or bound.

| Legacy ID | Original expression | Required current behavior |
| --- | --- | --- |
| ACTION-07 | #{changeDestination.load} | Load the authorized destination form and its current cargo values. |
| ACTION-10 | show.xhtml?faces-redirect=true | Click a claimed cargo and verify the same persisted details. |
| ACTION-11 | route.xhtml?faces-redirect=true | Reach route selection from an unrouted cargo's details. |
| ACTION-12 | #{changeDestinationDialog.showDialog(cargoNotRouted.trackingId)} | Open the current full-page destination editor from authorized cargo details. |
| ACTION-13 | #{changeDestinationDialog.handleReturn} | Return to the same cargo details after destination editing. |
| ACTION-15 | #{cargoDetails.load} | Load route-page cargo details for the selected cargo. |
| ACTION-16 | #{itinerarySelection.load} | Load actual route choices for the selected cargo. |
| ACTION-18 | #{itinerarySelection.load} | Reach route choices through the fixed legacy itinerary alias. |
| ACTION-20 | #{cargoDetails.load()} | Load authorized persisted cargo details. |
| ACTION-21 | selectItinerary.xhtml?faces-redirect=true | Open initial route selection from cargo details. |
| ACTION-22 | selectItinerary.xhtml?faces-redirect=true | Open replacement route selection from cargo details. |
| ACTION-24 | #{track.onTrackById} | Submit a valid/invalid tracking lookup. |
| ACTION-25 | #{track.onPointSelect} | Follow a live map cargo marker to its authorized details. |
| ACTION-45 | #{track.onTrackById} | Use the protected lookup reached through the legacy tracking entry. |

## Implementation-only controls: proposed retirement with replacement proof

Retirement is conditional on replacement and negative-entry evidence; listing a replacement here is not proof it passes.

| Legacy ID | Original expression | Replacement capability that must be covered |
| --- | --- | --- |
| ACTION-08 | #{changeDestinationDialog.cancel()} | Modal cancel callback → leave the full-page editor without applying changes. |
| ACTION-23 | #{track.completeTracking} | Tracking autocomplete callback → validated typed lookup plus authorized cargo-list navigation. |
| ACTION-26 | #{bookingBackingBean.deadlineUpdated} | Deadline AJAX callback → strict deadline validation on the current booking form. |
| ACTION-27 | booking-destination | Booking wizard next-step transition → single-page origin/destination/deadline form. |
| ACTION-28 | /admin/dashboard | Booking wizard cancel outcome → leave booking without creating a cargo. |
| ACTION-30 | booking | Booking wizard back transition → edit fields on the same page. |
| ACTION-31 | /admin/dashboard | Booking wizard cancel outcome → leave booking without creating a cargo. |
| ACTION-32 | booking-date | Booking wizard date-step transition → single-page deadline field and validation. |
| ACTION-33 | /admin/dashboard | Booking wizard cancel outcome → leave booking without creating a cargo. |
| ACTION-34 | booking-destination | Booking wizard destination-step transition → single-page destination selection. |
| ACTION-35 | pm:secondScreen?transition=flip | PrimeFaces Mobile screen flip → single-page handling form. |
| ACTION-36 | #{eventBackingBean.updateVoyage} | Mobile cargo-selection/voyage AJAX helper → valid selected cargo, corresponding known-voyage choices and LOAD/UNLOAD requirements. |
| ACTION-37 | #{eventBackingBean.updateListener} | Mobile location/port-listener callback → valid required location selection in the current form. |
| ACTION-38 | #{eventBackingBean.updateListenerEvent} | Mobile event-listener callback → current event selection, LOAD/UNLOAD voyage requirements and clearing/ignoring voyage for other event types. |
| ACTION-39 | #{eventBackingBean.updateListenerEvent} | Mobile voyage-selector listener → known-voyage validation, LOAD/UNLOAD requirements and clearing/ignoring voyage for other event types. |
| ACTION-40 | pm:firstScreen?transition=flip | PrimeFaces Mobile back-screen flip → edit fields on the same page. |
| ACTION-42 | #{eventBackingBean.timeSet()} | Time-picker callback → strict typed completion-time validation. |
| ACTION-43 | #{holderBean.initFlow} | Mobile Faces flow initializer → authorized single-page handling entry. |
| ACTION-44 | #{track.getTrackingIds} | Tracking-ID dropdown getter → authorized cargo list and validated typed lookup. |

## Implementation after approval

Create the versioned contract/mapping schema with explicit proposed/mapped/retired states, machine-readable evidence requirements and fail-closed validation. Add regressions proving that a missing replacement, wrong role/session, failed retired POST denial or absent effect observation cannot be marked retired/satisfied. Regenerate reports and obtain separate review before changing gate results. Until then, keep the existing catalogue and BLOCKED outcomes unchanged.

## Alternative

Keep strict framework-level callback compatibility as the acceptance basis. That requires restoring or emulating the removed dialogs, wizard transitions, autocomplete and mobile flow hooks, or retaining their BLOCKED state. This adds implementation/testing scope without an identified user capability benefit; it is not recommended.
