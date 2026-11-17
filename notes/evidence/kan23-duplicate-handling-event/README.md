# KAN-23 duplicate handling-event replay observation

A fresh isolated candidate runtime replayed the same operator CUSTOMS report (USCHI, completion time 2030-01-03 10:00) after the first submission had completed. The repeat was submitted through the handling REST endpoint using the same cargo and event fields.

Results: the replay added one handling-event row; each of `HandlingEventRegistrationAttemptQueue` and `CargoHandledQueue` recorded one new message and one acknowledgement. The registration service and worker, cargo-handled consumer, inspection audit and inspection service each ran once for the replay. The delivery projection remained `IN_PORT` at `USCHI`. This establishes that duplicate reports are not suppressed before persistence or downstream processing; the delivery view can remain unchanged even as duplicate records and work are created.

The full isolated fixture passed 777 runtime checks and 52 Java 25 Maven tests (0 failures/errors/skips). The container and private fixture files were removed; cleanup errors: none. Shared `ai-modernization-kan18` and Jenkins remained running and were not modified. The duplicate-specific counters are in [summary.json](summary.json).

This is a behavior observation, not an approval to change replay policy. It does not prove equal-time ordering or concurrent duplicate handling.
