# KAN-19 responsive handling workflow

1 November 2026. /mobile.xhtml is now a direct, authenticated Faces/PrimeFaces form rather than a redirect into the obsolete PrimeFaces Mobile flow. Only Operator/Administrator can open or submit it; Reader has no handling link and direct/forged requests are denied. Existing servlet CSRF and EJB service roles protect submission independently of visibility.

Preserved legacy eligibility: routed and unclaimed cargo only. Eligibility and known locations/types/voyages are rechecked at submission, not trusted from a posted dropdown. LOAD/UNLOAD require a known voyage. Completion text must be a real calendar value in YYYY-MM-DD HH:mm; no new future/past-time policy is introduced, and the existing service interprets it in server-local time. Native REST validation rules are not claimed fixed by the stricter UI.

A transactional read facade provides voyage identifiers; no persistent entity crosses the presentation boundary. The form calls the existing role-restricted HandlingReportService and shared JMS pipeline. Acceptance is displayed as “Accepted for processing. Check cargo details for the result.” It does not imply async processing has completed. Broker retries/TTL/dead-letter/final error UX remain separate work.

Browser verification includes 390px layout, Reader direct/forged denial, missing CSRF, invalid calendar and missing required voyage, distinct Operator/Administrator CUSTOMS locations/times and positive LOAD with a voyage. Separate Reader REST snapshots verify actual asynchronous location and transport-state changes, not just submission acknowledgement. Exact final results and input hashes are under notes/evidence/kan-19-mobile.

Use python3 tests/browser-workflows/run_browser.py. The complete supported candidate UI suite includes booking, routing/rerouting, destination, live tracking/logout/expiry and this responsive handling page. Older flow-only eventLogger resources remain blocked; legacy bookmark aliases/direct-link parity are tracked separately in KAN-20. Full platform/security acceptance, independent KAN-14 database/queue/audit absence and broader validation/resilience remain open.

No original source, historical GlassFish data, Jenkins configuration or synced sources are modified. Tests use disposable runtimes/network and private per-run credentials removed afterward.
