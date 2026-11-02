# Current-UI acceptance decision — 2 November 2026

Decision: approved for implementation.

The user answered "Approve recommended approach" to the explicit question asking whether KAN-15 acceptance should follow current user capabilities while preserving the complete legacy inventory. The question linked specifications/current-ui-access-acceptance-proposal.md and stated that obsolete hooks become RETIRED only after replacement and retired-entry denial tests pass; RETIRED never counts as PASS; roles, session/CSRF checks and denied-write effects remain required.

Approved proposal version SHA-256:710b00d37001276e8bd60d806f9fe21ea66a39b7b47ae465122ca78da931da5a (commit0b50e188b856e6136ee884ff623cd22f9fa64d5f). Its independent review is notes/agent-reviews/2026-11-02-current-ui-acceptance-proposal-review.json. That review approved documentation; this separate record supplies the subsequent human decision.

Implementation is still pending. Preserve all502 historical definitions/results, create a versioned current-capability gate/mapping and fail-closed retirement requirements, keep unverified internal/worker boundaries blocked, and independently review every resulting change before publication. Approval does not itself satisfy a replacement test, retire an item, accept security gaps or authorize production deployment.
