# Replacement capability evidence

The current gate supports cancel-editor, booking-cancel and tracking-discovery as fresh replacement capabilities.

For cancellation, Operator and Administrator change unsaved fields in the real rendered form and leave through the actual cargo-list link. Editor cancellation returns to the selected cargo and verifies its saved details. Booking cancellation verifies that leaving the completed form creates no cargo. Reader is denied the editing source and retains access to readable return pages. Anonymous source and return requests encounter the configured login boundary.

A private stdin/stdout handshake asks the host to capture the existing independent observer immediately before and after each actor's cancellation. Requests use ordered IDs and a fixed stage allowlist, and snapshots carry the owned fixture ID and exact stage. The 300-second browser execution budget propagates through capture, with each observer capture capped at 30 seconds and bounded process cleanup afterward. Credentials are written over stdin to the browser's private tmpfs before the handshake begins.

The snapshots require unchanged database and queue state. Exactly one CargoMonitoringService#getAllCargo read is expected for independent readback, while every other invocation counter must match. Tracking discovery composes the fresh claimed-list navigation and typed lookup proofs for the same cargo, including invalid inputs, CSRF checks and anonymous denials.

The fresh fixture passed 661 native and 619 browser checks, with 137 unit checks passing. Current coverage is **392 PASS / 78 BLOCKED**, comprising 32 replacement and 46 internal cases. All 76 retirement checks remain BLOCKED and gate exit is 2.

See [sanitized results](../../notes/evidence/kan-15-replacements-first/validation.json) and [independent review](../../notes/agent-reviews/2026-11-05-kan15-replacements-first-review.json).
