# AI modernization project instructions

- Treat synced sources/ references and experiments/legacy-cargotracker as read-only. Preserve unrelated work, credentials and the historical runtime. Make candidate changes separately.
- For substantive code, configuration, test or documentation changes, follow [the separate-agent review workflow](docs/agent-review-workflow.md). Use a separate reviewer agent, ideally with fresh context; author self-review does not satisfy this requirement. User authorization for separate reviewer agents is recorded 1 November 2026.
- Resolve material findings and record review evidence in repository/Jira before task completion/publication. Do not claim historical work was independently reviewed when it was not.
- Minor non-semantic wording/formatting changes can use the documented lighter check. Do not create extra user approval steps for routine corrections; escalate actual scope/business/access-policy changes or accepted material limitations.
- Publishing, deployment and service changes still require the task's applicable authorization. Never include secrets, caches, ignored source clones or private runtime data in Git/review evidence.
- Standing publication authorization from the user (1 November 2026): after independent agent review approves the changes and required checks pass, commit and push without asking again. Report the independent review outcome and publication result. Preserve other task-specific deployment restrictions.
- User execution rule (1 November 2026): continue automatically to the next Jira task after successful independent review, checks and commit/push; report the active Jira ticket. Terminate any task exceeding 30 minutes, report its state in detail and wait for user input. This replaces the earlier 10-minute limit.
