# KAN-18 candidate regression after KAN-23 ordering change

Date: 2026-11-23. Source revision: a20c212 (KAN-23 request-ID replay decision and equal-completion ordering).

A fresh isolated candidate runtime was built from the pushed source using unique run ID kan18-kan23-history-20261123. The existing candidate-runtime gate passed **808/808** checks. Its pinned Java 25 domain and characterization suite passed **64 tests**, with zero failures, errors, or skips; the inherited empty TODO remains explicitly reported. Flyway reached schema version 6.

The task-owned app container, PostgreSQL Compose resources, image and private files were removed; cleanup errors: none. The independent progress monitor verified that shared ai-modernization-kan18 and Jenkins retained their starting container IDs and start times and remained running. The working tree remained clean.

The machine-readable summary is in [summary.json](summary.json). Independent review approved with no actionable findings: [review record](../../agent-reviews/2026-11-23-kan18-regression-evidence-review.md). The complete local runner receipt remains in the ignored .work path recorded there and is SHA-256 pinned. This broad runtime regression does not replace the focused unit assertion for equal-completion ordering, nor does it constitute the separate Chromium browser suite or close KAN-18 overall.
