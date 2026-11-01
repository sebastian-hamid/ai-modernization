# Filtered cargo and About views (KAN-15)

## Functional behavior

Reader, Operator and Administrator can open the cargo dashboard and its Routed cargo, Unrouted cargo, Claimed cargo and Cargo workflows links. Anonymous direct access goes to fixed login before loading cargo. The filtered pages display tracking ID, origin and destination, with a controlled message for an empty result.

The existing ListCargo predicates are preserved:
- Routed cargo: itinerary has legs and the cargo is not claimed. This includes assigned itineraries currently marked MISROUTED; it does not mean a route necessarily satisfies the current destination/deadline.
- Unrouted cargo: itinerary has no legs.
- Claimed cargo: transport status is CLAIMED.

Tracking links open cargo details for all permitted read roles. In the old unrouted fragment links went straight to the operator-only route view; route assignment is now reached through the existing authorized control on details. No claim/unclaim action or new mutation permission is added.

The protected Cargo workflows page describes read versus operator actions. Public About remains accessible without identity, contains no cargo data and now accurately says tracking requires sign-in. The previous no-login tracking description is removed.

## Architecture and access

The three list pages use the existing request-scoped ListCargo bean and transactional, role-checked facade/DTO assembly. ListCargo's legacy routedUnclaimedCargos, notRoutedCargos and claimedCargos methods remain unchanged. No domain/business-service behavior is changed.

Four exact paths are added to the manifest with Reader/Operator/Administrator roles: admin/about.xhtml, admin/listRouted.xhtml, admin/listNotRouted.xhtml and admin/listClaimed.xhtml. Existing access filtering runs before Faces rendering and bean construction. Public About/index permissions remain unchanged. Navigation is server-rendered and the filter bar wraps at narrow widths.

Canonical live bindings add six page surfaces: PAGE-03/06/07/08/22/24. Active-role/public cases and protected-page logout/expiry cases extend the 55 API/private definitions to 103 bound definitions; the other 399 remain unsupported/BLOCKED and full gate exit stays 2.

## Verification and limitations

From WSL repository root:

    python3 tests/browser-workflows/run_browser.py
    python3 tests/security/run_candidate_contracts.py --live-subset
    python3 -m unittest discover -s tests/security -p 'test_*.py' -v

Runtime checks compare complete rendered tracking-ID sets against a separate authenticated cargo snapshot, rather than accepting page 200 alone. They verify fixed anonymous login navigation, public no-cargo content and per-role logout/expiry page replay inside the existing independent-effect windows. Native identities are verified by the existing fixture.

Browser checks render each list and compare exact IDs for all three roles, exercise empty results and explicitly set 390px for each role's list checks. An actual unload followed by claim on the newly booked/routed fixture is persisted and observed by Reader before all roles' filtered lists are rechecked, including absence from routed-unclaimed and presence in claimed. Existing booking/routing/mobile/live/session tests remain in the regression.

Independent review caught the initial accidental change from routed-unclaimed to all routed. Corrected both page and test predicates before final execution; the deliberately interrupted earlier run is retained as non-passing evidence. An explicit viewport setup removes ambiguity about which roles were checked at mobile width.

Sanitized final reports and exact input hashes are under notes/evidence/kan-15-read-views; review is separate. H2/Chromium coverage and one inherited empty domain TODO remain. These bindings do not cover every old callback, JSF replay variant, worker/import or retry/restart behavior, and full denied-effect acceptance stays incomplete. Historical sources/runtime and synced references remain untouched.
