# KAN-18 candidate and browser regression after KAN-23

Date: 23 November 2026  
Run ID: kan15-kan18-post-kan23-browser-20261123  
Repository revision at run start: 4d7ad6e

A fresh isolated integrated run verified the current candidate after the KAN-23 handling-history ordering change. The candidate-runtime gate passed **808/808 checks**; Java 25 domain and characterization tests passed **64/64** (zero failures, errors, or skips); Flyway reached schema V6. The real Chromium workflow passed **970/970 checks**.

The harness removed its candidate and browser containers, PostgreSQL Compose project, owned networks and images, and generated private files. Cleanup reported no errors. The independent progress monitor confirmed the shared KAN-18 and Jenkins services remained running throughout.

Sanitized counts and cleanup facts are in [summary.json](summary.json). Ignored local receipts remain under .work/kan15-kan18-post-kan23-browser-20261123/ and are SHA-256 pinned in the summary; their raw contents are not committed.

This is disposable local test evidence, not production deployment evidence. The separate generated-sample migration rehearsal is not proof about arbitrary data. The user confirmed that no retained legacy dataset exists, so actual-data profiling and import are not applicable to the current scope. This regression does not by itself close KAN-18.
