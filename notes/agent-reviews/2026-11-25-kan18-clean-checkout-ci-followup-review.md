# Independent review — KAN-18 clean-checkout CI portability follow-up

Date: 25 November 2026
Reviewer: /root/review_clean_checkout_ci_followup
Verdict: APPROVED; no actionable findings.

## Scope

The reviewer inspected the changes to tests/security/current_capabilities.py, tests/security/replay_bg06_scoped_gate.py, tests/candidate-runtime/test_harness.py, notes/setup-status.md and notes/ai-task-log.md.

The ACTION-32 review record's normalized LF hash matches the tracked document (59dad6d6126155f9e223fe933e9ce7e4ff6bb173372c712717215c263ee12f9b), while its original receipt-recorded hash (e6b6d16e8f6d74b9ee1f5cd2fece44503fd44c323ee28b2b5d033c34e08bb0b5) remains checked separately. The BG-06 source-hash compatibility alias is restricted to HandlingQuarantineConfiguration.java and only applies when the reviewed receipt contains the exact original mixed-line-ending hash (f80ad228d44f366dbb9091becb66621e8c5962093a3dd9f7aca9e8234220fbfa); the tracked LF hash (1c9ab837c3c7834047e20ccd41e2500c26a6091ad728083e340cbfe0d596edcc) is verified. Other paths and hashes retain exact comparison. The candidate cleanup test directs its log to the test's temporary directory.

## Verification and limitation

The author ran the changed focused suites from a clean simulated SCM checkout with the pinned legacy source revision. Results: 8 setup, 17 contract-engine, 70 current-capability, 13 replacement, 5 staged-return, 16 candidate-harness and 3 security-runtime-harness tests passed; git diff --check passed.

The independent reviewer could not confirm the aggregate test totals within the 30-second review run window. Jenkins build #10 on b03fe4c fetched the pinned legacy revision but failed in the security suite before later candidate build stages. This review approves the code/evidence portability corrections; it does not claim the Jenkins pipeline has passed or close KAN-18.
