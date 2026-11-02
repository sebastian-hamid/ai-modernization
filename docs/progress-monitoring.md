# Independent progress monitoring

User clarification, 2 November 2026: the old 30-minute rule was intended to prevent loops and wasted credits, not to stop productive work at an arbitrary elapsed time. It is superseded by this workflow. Existing publication, independent review, access and deployment rules remain in effect.

## Roles and limits

The author continues authorized work and reports the active Jira ticket. Start a separate read-only monitor agent for sustained implementation. Give it the task, acceptance criteria, starting revision, planned next step and available evidence. The monitor must not be the author. It may also review a change it did not author, but progress monitoring alone is not code approval.

This is cooperative supervision within the active agent session. The monitor does not automatically see every tool call, private reasoning or usage balance, cannot guarantee a spending cap, and is not a persistent watchdog after the session ends. The author must provide checkpoints and obey hold recommendations. If the monitor becomes unavailable, report that and restore independent monitoring before sustained unattended work; use bounded checks to preserve state in the meantime.

## Low-overhead checkpoints

Send concise checkpoints at task/approach changes, failures, long-running command launches, test completion and before retrying. Include the command/session identifier when available, elapsed time, expected duration, last observable progress, result, changed hypothesis and next decision. Include file/evidence paths rather than large repeated logs.

During a long running step, provide a checkpoint roughly every five minutes or sooner on failure. The monitor should stay quiet while evidence shows normal progress. Do not create continuous polling, duplicate full suites or a chain of monitor agents merely to supervise the work. Normal user-facing progress updates still apply.

## Signals and response

- Repeating the same failed action without a changed hypothesis or new evidence: request a hold before another equivalent retry. After two equivalent failures, a further attempt requires an explicit changed approach and monitor assessment.
- Re-running passing suites without a relevant change or unresolved concern: flag unnecessary work.
- A command exceeds its expected duration with unchanged logs/output/state: inspect once using a bounded read-only check. If there is still no evidence of progress, recommend stopping the owned command and diagnosing it.
- Roughly ten minutes with no measurable task progress: trigger a diagnostic review, not another blanket task deadline. A known quiet build/test phase may continue with concrete state evidence and an expected completion bound.
- Scope expansion, unbounded retries, repeated planning without implementation or evidence, or growing cost without useful results: recommend narrowing or holding the work.

A hold recommendation must identify the stalled step, supporting evidence and a concrete next action. The author stops the affected owned work at the next safe boundary, preserves useful logs and changes approach. Cancel only task-owned processes/resources; preserve shared services and existing work. Existing fixture cleanup requirements apply.

If the block persists after a bounded diagnostic/change of approach, or progress requires access, a business decision or accepted material limitation, stop and tell the user what was attempted, what remains, and the smallest input needed. Do not reset retries by renaming a step or spawning another author/reviewer. A task exceeding 30 minutes is allowed when evidence shows productive progress.

## Verification and reporting

Keep individual tool/process timeouts and explicit retry bounds appropriate to the step. A monitor does not replace them. Record significant hold decisions and resolutions in task evidence; ordinary healthy checkpoints need no permanent log dump. Report independent code/document review separately from progress monitoring. After a successful review, checks and publication, continue to the next authorized task without a fresh elapsed-time approval.
