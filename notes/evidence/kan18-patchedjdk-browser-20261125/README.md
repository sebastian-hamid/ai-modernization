# KAN-18 patched Java candidate and browser regression

Date: 25 November 2026
Run ID: kan15-kan18-patchedjdk-browser-20261125
Repository revision at run start: 4d7ad6e (patches under review were uncommitted).

A fresh integrated run used Maven 3.10.0 with Temurin 25.0.5.1+2. The candidate-runtime gate passed **808/808 checks**; Java 25 domain and characterization tests passed **64/64** (zero failures, errors, or skips); Flyway reached schema V6. The real Chromium workflow passed **970/970 checks**.

The harness removed its candidate and browser containers, PostgreSQL Compose project, owned networks and images, and generated private files. Cleanup reported no errors. The progress monitor confirmed that shared KAN-18 and Jenkins services remained running throughout.

Sanitized counts, cleanup facts, and SHA-256 pins are in [summary.json](summary.json). Ignored local receipts remain under .work/kan15-kan18-patchedjdk-browser-20261125/ and are not committed.

This is disposable local test evidence, not production deployment evidence. The separate generated-sample migration rehearsal is not proof about arbitrary data. The user confirmed no retained legacy dataset exists, so actual-data profiling and import are not applicable to the current scope. This regression does not by itself close KAN-18.
