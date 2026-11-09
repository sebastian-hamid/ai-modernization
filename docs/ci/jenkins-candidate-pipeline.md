# Jenkins candidate CI (KAN-29)

The local legacy baseline job remains unchanged: `ai-modernization-baseline` continues to run its pinned historical-source snapshot on its existing exclusive Java 8 agent. Candidate SCM CI is a separate job, node and workspace.

## SCM and trigger

- Job: `ai-modernization-candidate`, Pipeline script from SCM.
- Public remote: `https://github.com/sebastian-hamid/ai-modernization.git`, branch `main`.
- Pipeline path: `candidate/cargotracker/Jenkinsfile`.
- Jenkins SCM polling is declared in `candidate/cargotracker/Jenkinsfile` as `H/15 * * * *` (approximately every 15 minutes); no inbound GitHub webhook and no GitHub credential. The controller remains published only on localhost. The scoped registration script queues the first manual build; that run installs the Pipeline trigger for later polls.
- The Pipeline checks out the selected SCM revision on the candidate agent, verifies that the checked-out HEAD matches the Git plugin's revision, prints `BUILD_GIT_REVISION`, sets the Jenkins build description to the short hash and archives the complete revision in `ci-results/candidate/revision.txt`.

This is a single-branch Pipeline job, not a multibranch/PR build. Jenkins official docs describe Pipeline script from SCM, its script path, and SCM polling as the trigger for changes; `checkout scm` checks out the triggering revision.

## Candidate agent boundary

The `ai-modernization-candidate-secure` node (label `ai-modernization-candidate`) is exclusive, with one executor and a separate named workspace volume. Its image is built from the repository's existing pinned Maven/JDK 25.0.5 image digest plus the pinned Java 21 remoting jar, Git and Python 3. The agent connects to Jenkins over WebSocket on the existing private Compose network. It has no Docker socket, privileged mode, published ports, application credentials, database credentials, or GitHub credential. The public GitHub checkout and Maven repository downloads require outbound network access.

The historical `ai-modernization-baseline` job/node and controller executor setting are not altered. The original candidate node identity has been rotated; the current inbound secret stays in the ignored, mode-600 local secret file.

## Build and gates

The candidate Jenkinsfile runs:
1. SCM checkout, revision assertion and toolchain version report.
2. Setup regression tests.
3. Four checkout-safe Python security-contract suites and isolated runtime-harness regression tests. The historical `tests/security/test_live_subset.py` is excluded because its inventory-regeneration case requires the ignored `experiments/legacy-cargotracker` reference tree, which is intentionally absent from the SCM checkout. Run that suite only in the local repository where the protected reference is available.
4. Candidate security-module build.
5. Candidate Cargo Tracker Maven verification and domain tests.
6. Required WAR, security JAR, revision and non-empty JUnit report presence checks.
7. JUnit publication and fingerprinted archive of the revision, WAR, security JAR and test reports.

The Python suites in CI test contract and harness logic. Jenkins publishes JUnit reports and fingerprints available artifacts; successful runs explicitly require the WAR, security JAR, revision file and at least one non-empty JUnit XML report. Empty report/archive globs do not hide an earlier failed stage. They do not substitute for the live 502-case access gate, WildFly runtime/browser workflows, database/queue side-effect observers, or full security acceptance. The agent intentionally has no Docker socket, so runtime fixtures that create containers remain separate local verification jobs. KAN-15 and KAN-18 acceptance stays open until those required live checks pass.

## Local configuration

Review `infrastructure/jenkins-agent/register-candidate.groovy` before applying it. The one-time controller setup creates only the named candidate job/node and refuses to replace a same-named item with an unexpected type or description. Polling is versioned in the Declarative Jenkinsfile, avoiding controller-side trigger mutation. If the first build fails before Jenkins loads the Jenkinsfile, polling has not been installed yet; after fixing the cause, use Build Now once and verify the job's polling trigger before relying on automatic updates. It stores the node secret in the ignored Jenkins-home bootstrap folder; the deployment procedure copies it to ignored `.work/jenkins-ci/candidate-secrets/agent-secret` with mode 600 for the candidate Compose service. Never print, commit, archive, or include it in reviewer evidence.

Build and start only the candidate agent using the steps recorded in `notes/setup-status.md`; do not restart or clean up the baseline agent or Jenkins volume. After the SCM job passes, record its commit, test counts, JUnit results and artifact fingerprints in `notes/evidence/kan-29-jenkins-candidate/`.

## References

- [Jenkins: Pipeline script from SCM](https://www.jenkins.io/doc/book/pipeline/getting-started/)
- [Jenkins: Pipeline syntax and triggers](https://www.jenkins.io/doc/book/pipeline/syntax/)
- [Official Maven image](https://hub.docker.com/_/maven)
