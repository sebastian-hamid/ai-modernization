# Reusable skills

## Legacy Java baseline

Created 26 October 2026 from the verified recovery, runtime and CI workflow in this repository.

- Versioned source: [skills/legacy-java-baseline/SKILL.md](../skills/legacy-java-baseline/SKILL.md).
- Personal installation for this Windows Codex environment: C:\Users\yasinrdp\.codex\skills\legacy-java-baseline.
- Invoke as $legacy-java-baseline.
- Normal automatic skill selection is left enabled.
- The installed and versioned copies were validated and checked to be byte-identical at creation.

The personal folder makes the skill reusable across projects in this Codex environment. The repository copy is the maintained source for review and version history; the personal folder is its installed copy. There is no automatic synchronization: after editing the maintained source, validate it and copy its files to the personal installation.

The WSL shell used to run the lab is distinct from this Windows Codex environment. No separate skill installation was made into a WSL user's Codex home.

The skill contains instructions and UI metadata only. It does not install software, change services, access credentials or invoke the project's scripts merely by being present. It guides the agent when a matching task is requested. Project state, exact versions, images and commands remain in this repository's runbooks and scripts.

Validation used the skill-creator quick validator. Review also checked the invocation boundaries: recovering an existing legacy Java baseline is in scope; ordinary greenfield Java work is not. No shared helper scripts were added because the current executable recovery scripts are specific to this lab.
