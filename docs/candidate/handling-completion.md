# Handling completion-time validation (KAN-15 ACTION-42)

The current mobile handling workflow validates completion time on the server. This checkpoint exercises the actual form with Operator and Administrator sessions, then confirms the form is denied for Reader and Anonymous sessions.

## Verified behavior

For both allowed actors, browser submissions reject an impossible calendar date, malformed syntax, a value missing minutes, hour 24, minute 60, and an empty required value. The empty value produces the JSF required-field validation error; other invalid values produce the completion-time parser error. Each rejection is checked against a settled before/after effects snapshot and no acceptance banner is allowed. Reader and Anonymous access to the current handling form is denied with required access evidence. (These completion-group cases verify access denial; they do not claim to submit a completion POST for denied actors.)

A valid positive control composes the same-fixture persisted CUSTOMS event from ACTION-38. It verifies the cargo remains routed and explicitly does not claim a second handling submission. An earlier fixture attempt exposed a correlated MisdirectedCargoQueue add/acknowledgement and MisdirectedCargoConsumer#onMessage derivative on the Operator positive event. The verifier admits only the exact zero-or-one correlated derivative, with settled queue depths and all unrelated queue and call deltas unchanged. In the accepted attempt 5, both Operator and Administrator samples had zero misdirection deltas.

## Validation result

Attempt 5 passed 661 native checks and 823 browser checks with no browser assertion failures. All four ACTION-42 role cases passed, as did the four cases each for handling-event and handling-voyage. The fresh current gate is 424 PASS / 46 BLOCKED; the preserved historical audit is 324 PASS / 178 BLOCKED; retirement remains 76 BLOCKED. The overall gate exit is 2 because unrelated current and retirement cases remain blocked. Owned fixture cleanup was verified.

Earlier fixture attempts and the sanitized machine-readable result are recorded in validation evidence. Private .work outputs are not part of this evidence.

Independent publication review is pending.
