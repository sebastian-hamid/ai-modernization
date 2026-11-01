# Separate-agent review workflow

Approved by the user on 1 November 2026. Applies to substantive code, configuration, test, functional, architecture and technical documentation changes in this project. This workflow supplements the approved proposal and task acceptance criteria; it does not authorize deployment, publication or changes to agreed scope/access rules.

## Standard sequence

1. **Author:** make a concrete, reviewable change with an exact file/diff scope, relevant source/test evidence and known limits. Preserve original historical sources, synced references, unrelated work and credentials.
2. **Separate reviewer agent:** review in a fresh context, preferably without the author's conversation history. Give the reviewer the task/acceptance criteria, approved decisions, changed files/diff, source revision and evidence locations. Do not supply a desired verdict. The reviewer must not be the author agent for that change. A different model/product is optional, not required.
3. **Author:** address findings, run appropriate verification and record why any finding is rejected or deferred. Send changed material back to the reviewer when a correction affects correctness, safety, access policy or the original finding. Avoid repeating unaffected test suites without a reason.
4. **Reviewer:** assess corrections and return a clear verdict with remaining findings and verification limitations. A clean review is not proof of exhaustive security or test coverage.
5. **Task closure:** store the review record and link it in Jira and, when available, the commit/PR. Resolve material findings before marking the task Done. Leave In Review when reviewer work or explicitly required user acceptance remains outstanding.

## Review responsibilities

For documentation, verify functional workflows and business rules, current-versus-target distinctions, architecture/data/event flows, technical instructions, contradictions, source citations and the evidence behind every claim labeled verified. Flag omissions and assumptions; static source declarations are not runtime test results.

For code/configuration/tests, inspect correctness, failure paths, authentication/authorization, unintended side effects, compatibility, data migration/recovery, secret handling, test relevance and documentation impact. Verify tests execute and assertions test intended behavior. Do not accept the author's passing-test summary without inspecting the relevant evidence or explicitly marking it unverified.

Report actionable findings with severity, file/line or section, supporting evidence, user impact and a recommended correction. Separate confirmed defects from questions, suggestions and unverified concerns. Record reviewed revision/input hashes, reviewer identity/agent identifier, checks actually performed, findings, author responses, follow-up checks and final verdict. Do not claim a review happened if no separate reviewer was used.

## Authority and scope

- Reviewers are read-only by default: inspect files and perform necessary safe checks, but do not edit deliverables, publish, message others or modify services unless that work is separately assigned and authorized. Disclose checks that could mutate fixtures before executing them; use isolated disposable fixtures within the task's authorization.
- Material findings include defects affecting correctness, approved requirements, access/security, data integrity, recovery or materially inaccurate documentation. They must be fixed, demonstrated inapplicable with evidence, or explicitly accepted as limitations by the user. Do not silently downgrade a finding to close the task.
- Routine corrections and verification proceed without repeatedly asking the user. The user approves business-rule/access-policy/scope changes and accepted material limitations. User approval does not imply a separate AI review occurred, and AI review does not replace required user decisions.
- If reviewer and author disagree on a material point, document both positions and escalate the concrete decision to the user. Do not ask another reviewer repeatedly to obtain a preferred verdict.
- The author may use another agent supplied by the environment; if separate review is unavailable, record that limitation, complete unaffected work and leave the review pending. An author self-check is not a substitute.
- Minor spelling, formatting or link-label edits with no semantic, policy or executable change can use a lighter author check. Document the reason for the exception. API/signature, security, migration and workflow changes are substantive regardless of diff size.

## Review record template

- Task and scope; source/input revision or hashes.
- Author and separate reviewer agent identifiers.
- Review date; checks/evidence actually inspected.
- Findings with severity, location, impact and recommendation.
- Author response/correction and follow-up verification for each finding.
- Verdict: changes requested / reviewed with disclosed non-material notes / no remaining material findings.
- Remaining gaps, required user decisions, and Jira/commit/PR links.

## Adoption

Apply this workflow to future substantive changes and substantive pending changes before closure/publication. Do not retroactively claim separate review for historical completed work. KAN-12 user documentation approval is recorded on 1 November 2026; any remaining separate-agent review is tracked distinctly from that approval. Exact automation or CI enforcement is not implemented by writing this policy.
