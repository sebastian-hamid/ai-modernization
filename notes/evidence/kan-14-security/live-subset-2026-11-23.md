# KAN-14 fresh candidate security live-subset run

Date: 23 November 2026

## Run scope

A fresh isolated candidate-runtime and browser run executed the KAN-14 live-subset contract adapter. Run ID: `kan15-kan14-security-20261123`. The candidate adapter invokes the repository browser workflow and only promotes contract rows supported by its fresh server-identity, browser, and independent-effects observations. Unsupported cases remain BLOCKED.

The run used the existing disposable PostgreSQL/Flyway candidate fixture. Flyway reached V6. The runner reported 808/808 candidate checks passed, 63 domain tests passed (0 failures, errors, or skips), and 970/970 Chromium checks passed. It removed its owned candidate and browser containers, private credentials, PostgreSQL Compose project, network, and image. Shared KAN-18 and Jenkins services were preserved.

## KAN-14 contract result

The generated 502-case contract catalogue reported:

| Outcome | Cases |
| --- | ---: |
| PASS | 317 |
| FAIL | 7 |
| BLOCKED | 178 |

The adapter exited 1 because the contract catalogue contains FAIL results; this is not an all-green KAN-14 acceptance result. All seven failures are PAGE-25 cases: anonymous access and logged-out/expired Reader, Operator, and Administrator access to `/cargo-tracker/public/track.xhtml`. The original KAN-12 inventory expects this route to deny anonymous and revoked sessions. The current candidate navigation documentation describes typed public tracking. This run retains all seven results as FAIL and does not edit the original inventory or claim that these cases passed. Resolve the inventory/current-behavior discrepancy through the existing current-capability mapping; do not silently change historical expectations.

All 178 BLOCKED cases report that the required candidate adapter is unavailable. No outcome was inferred for them.

## Evidence and limits

The private, ignored raw receipts were inspected for this summary; their SHA-256 hashes are:

- Candidate runtime receipt: `c592bd0a0f8c79ee636cb3ee119651170dadaf8c6bbcf40d5493f0289bd86461`
- Browser workflow receipt: `b01462458a409cae5eb613d802fcfca1b2057aefbaf978ea9b75d47e7047c388`
- KAN-14 contract result: `e4600e86c87607917687da1be155e2a3a35566dd3bd2af8c3c9ddd3c7ea494ae`

The corresponding run files remain only under ignored `.work/kan15-kan14-security-20261123/` and `.work/kan14-live-20261123/`; no credentials or raw row data are committed. This fresh bounded execution does not complete the 502-case catalogue or KAN-14 acceptance. KAN-14 remains In Review.
