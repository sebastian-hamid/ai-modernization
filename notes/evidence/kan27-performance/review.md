# Independent review record — KAN-27

- Review date: 2026-11-21.
- Jira ticket: KAN-27, `[QA-03] Measure performance and agree regression thresholds`.
- User decision: the four synthetic cargo records are approved as an initial local regression workload. A review is triggered when a matching candidate p95 exceeds 120% of its baseline. These are investigation triggers, not release failures or SLOs.

## Reviewers and scope

### Initial evidence and threshold review

- Reviewer: independent agent `/root/review_kan27_performance`.
- Scope: initial report and user-approved threshold update; compared aggregate results with task run records, checked threshold arithmetic/mapping, start-up wording, limitations, and whether policy text matched the user's decision.
- Findings: stale startup counts, contradictory threshold approval wording, and duplicate limit entries. The author corrected them and sent the changes for re-review.
- Verdict: no remaining material findings. The reviewer verified the 120% calculations: catalogue sequential 19.692 ms, catalogue five-worker 39.336 ms, tracking sequential 63.132 ms, and tracking five-worker 120.072 ms.

### Reproduction package review

- Reviewer: independent agent `/root/review_kan27_reproduction`.
- Reviewed inputs: current working tree based on commit `8e0f698`, including the report, procedure, scripts, fixture image recipe, summary and raw rerun/start-up result JSON. SHA-256 values for reviewed inputs are listed below.
- Findings: one medium safety gap in the first draft (stale Compose volume/network reuse was not checked) and two low clarifications (cleanup guard behavior and app-only startup timing boundary), plus a duplicate limit entry.
- Author response: added collision checks for project-labeled containers, volumes and networks and exact generated volume/network names to both the procedure and startup runner; added strict shell mode and an explicit marker-validation branch before destructive cleanup; clarified that repeated app-only timings begin after the Compose command returns and full-stack timing includes Compose command overhead; removed the duplicate limit. The runner was exercised against an existing project and refused before changing resources.
- Follow-up verdict: approved; no remaining material findings. Reviewer verified the raw sample summaries and p95 values, threshold arithmetic, full-stack timing composition (5.748 + 5.925 + 1.459 + 16.656 = 29.788 seconds), and absence of credential values in committed result data. The reviewer noted that preflight checks and Compose startup are not atomic; the generated unique run IDs make that a non-material residual consideration for this local procedure.

## Author verification and remaining limits

- Four raw workload groups contain 100 timings each; recalculated count/min/p50/p95/max/mean values match the JSON summaries.
- The candidate reproduction run did not exceed any approved p95 review trigger.
- Python sources compile; result JSON parses; CLI help runs; existing-project collision check refuses safely.
- Candidate full-stack startup was measured once. Startup variability is not characterized. Startup and resource regression thresholds remain unapproved. Results remain a small, single-host synthetic baseline, not production capacity evidence.
- All task-owned containers, volumes, networks, private credentials and temporary images were removed after measurement. Shared Jenkins and KAN-18 services remained running.

## Reviewed input SHA-256

```text
README.md 53558a22718ea0f39f3fb0dfa1071d9e343b87a6639833020c1719db36344d03
REPRODUCE.md bd96cfce8854786af3d1ba4feaa6303b0956d1828318ff2d2e42c5d524555f8a
Dockerfile.candidate 1a947324fcd6c288364f29e1b476b195e16956f91120d81d14d7b8a510477c43
measure.py 58797cd7d072b05fe15612e712b2df169bf560e4a31ee049cbc4e9fd3c553d9c
measure_startup.py bbf487e7677d742fe2062a3a4be04100883c5eafc788b963c2b1ea4604aefaa0
prepare-secrets.py d107c0ee71d99c819844b2c47cff12e129fc244b56462faf9caef074c00505a8
summary.json reviewed working copy B22E50BFECF146A069000E27E6E1874186563A8C6315EF0F20575BCBED4ED6D4; Git index LF-normalized bytes 92181CBD185E562E5CA93CBDF431531263B74ABE62546C6BBB99FC0EA01D6726
candidate-rerun-20261121.json 64cf4d27977414785e6f805e45958c8fa3723ff7bb19356a4142b9ead1e47935
legacy-rerun-20261121.json 0e45491ae43467d37b4e886d81c7c33eae16d174c767f092bddc7315b3b57795
candidate-fullstack-startup-20261121.json a6973cd93d26759fe7ab16774ca3849b211e71634c3412ba5ccaceff2d613264
```