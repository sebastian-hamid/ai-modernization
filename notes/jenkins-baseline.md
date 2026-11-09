# Jenkins baseline pipeline
Verified 23 October 2026, Europe/Bratislava.

## Result and entry points
- [Baseline job](http://localhost:8080/job/ai-modernization-baseline/)
- [Successful build 1](http://localhost:8080/job/ai-modernization-baseline/1/)
- Result: SUCCESS in 99.495 seconds.
- JUnit results: 28 reported tests, zero failures/errors/skips: 24 domain + 4 Arquillian booking tests.
- ItineraryTest.testNextExpectedEvent is still an empty TODO; a passing count is not complete behavior coverage.
- Tracking, connected route candidates and the JMS-processed handling event smoke checks also passed.
- Jenkins archived the WAR, test reports, logs, recovered-dependency hashes and runtime correction provenance.
- [Recorded build summary](evidence/jenkins-build-1-summary.json), [console log](evidence/jenkins-build-1.log) and [JUnit result](evidence/jenkins-build-1-junit.xml).

## Agent and controller
- Existing Jenkins users, authentication and the named Jenkins home volume are preserved.
- A one-time local init script registered the job and agent; it did not read or replace an administrator password or disable authentication. It was moved out of init.groovy.d after successful application.
- Controller executors changed from 2 to 0; builds run on the separate ai-modernization-baseline node.
- The non-root agent has one executor, exclusive label ai-modernization-baseline, Java 21 remoting, Java 8/Maven builds and Python 3.
- Both base images are pinned by digest in infrastructure/jenkins-agent/Dockerfile.
- The agent has no Docker socket, Docker daemon, privileged mode or published ports.
- Only its own named workspace volume, a read-only pipeline source snapshot and its node-specific connection secret are mounted.
- Jenkins connection uses WebSocket over the existing private Docker network infrastructure_default. No new agent TCP port is published.
- The node-specific secret is stored privately under ignored .work/jenkins-ci/secrets and Jenkins home. It is not included in source snapshots, logs or archived artifacts.
- The original controller configuration backup is under ignored .work/jenkins-ci/controller-config-before.xml.
- infrastructure/jenkins-agent/register.groovy records the configuration applied. Controller-side applied copy: /var/jenkins_home/ai-modernization-bootstrap/bootstrap.applied.groovy.

## Pipeline stages
1. Load the read-only local snapshot into a clean agent workspace.
2. Clone and verify the exact application, PrimeFaces theme and build-plugin commits.
3. Rebuild the historical dependencies and package the unchanged application.
4. Enable the existing domain tests through a separate POM and require 24 clean results.
5. Prepare GlassFish 4.1 with the documented HK2-277 manifest-only correction, deploy the WAR, require four passing booking tests, and run HTTP workflow checks.
6. Stop the temporary server even if tests fail; publish reports and archive evidence.

The agent uses native Java/Maven processes for these steps. Docker-based developer commands remain available independently. Its temporary GlassFish uses the agent's private localhost:8080/4848; the existing demonstration app on Windows localhost:8081 is not replaced or used by CI.

Pipeline settings: no concurrent builds, 30-minute timeout, latest 10 build records retained, latest five sets of archived artifacts retained. Browser JavaScript, WebSocket presentation and CSV bulk handling are still outside coverage.

## Setup review — 26 October 2026
The reviewed baseline is versioned locally as baseline-v0.1.0. The Jenkinsfile now runs eight setup-tool regression checks before fetching upstream source. Snapshot inputs are exact and hashed, deleted inputs are removed, operational checks survive Python optimization, and artifact origin recording handles Maven repository context suffixes. Historical Jenkins archives remain unchanged; a provenance correction is documented in setup-review-2026-10-26.md.

## Run again
Sign in with your existing Jenkins account, open the baseline job and select Build Now.

The current job uses an inline copy of Jenkinsfile and a local snapshot so this uncommitted work could be verified without publishing it. It is not yet a GitHub-triggered pipeline, and it does not push source or statuses to GitHub.

After changing supporting scripts, refresh the source snapshot while the job is idle:

    python3 ci/update-local-snapshot.py

Then choose Build Now. Jenkinsfile edits also require updating the job's Pipeline script in Configure; refreshing the source snapshot alone does not change the installed inline definition. The source hashes used for build 1 are preserved in [its snapshot manifest](evidence/jenkins-build-1-source-snapshot.json).

To stop or resume only the agent:

    docker compose -p ai-modernization-ci -f infrastructure/compose.ci.yaml stop
    docker compose -p ai-modernization-ci -f infrastructure/compose.ci.yaml up -d

To rebuild its image after Dockerfile changes, use up -d --build while the job is idle. Keep the existing Jenkins controller network available.

## Re-create the local Jenkins configuration
The required plugins are workflow-job, workflow-cps, pipeline-model-definition and junit; all were already installed. The original controller Compose configuration remains infrastructure/compose.yaml.

For a new local controller or deliberate configuration update, while builds are idle:
1. Refresh the input snapshot and build infrastructure/compose.ci.yaml.
2. Create /var/jenkins_home/ai-modernization-bootstrap and copy the root Jenkinsfile there. Ensure that directory is writable by Jenkins UID 1000.
3. Copy infrastructure/jenkins-agent/register.groovy into /var/jenkins_home/init.groovy.d with a unique .groovy name, then restart the local controller.
4. Confirm ai-modernization-bootstrap/status.json exists. Copy its agent-secret file privately to .work/jenkins-ci/secrets/agent-secret, owned by WSL UID 1000 with permissions 600. Never print it.
5. Start the agent using the CI Compose command. The registration script queues the first build only when the job has no previous build.
6. Move the applied init script out of init.groovy.d to the bootstrap directory, using container root for that filesystem operation.

This setup procedure changes only this lab's named job/node and sets controller executors to zero; it preserves security configuration. The script refuses a same-named item of a different type. Review the source before deliberately applying it to a different Jenkins installation.

## Remaining work
- The setup is now reviewed and versioned locally as baseline-v0.1.0. Initial setup was uncommitted; the reviewed baseline-v0.1.0 release is now versioned locally. It has not been pushed.
- Once the scripts are in the desired GitHub branch, change the job to Pipeline script from SCM and add an explicit trigger if wanted.
- Handling lifecycle and negative-input characterization is expanded; see [handling-characterization.md](handling-characterization.md). Broader route randomness and final JMS retry/dead-letter behavior remain follow-ups.

Official references:
- [Jenkins node guidance](https://www.jenkins.io/doc/book/managing/nodes/)
- [Jenkins agent image and connection guidance](https://github.com/jenkinsci/docker-agents/blob/master/README_inbound-agent.md)

## Entrypoint and access review (27 October 2026)
The pipeline now includes 81 entrypoint contracts and archives ci-results/entrypoints/ observations and security findings. Expected overall count is 134 application cases, plus 10 tooling checks. A baseline pass is not security approval: the standalone --require-access-control gate currently fails on anonymous operational access. See [coverage review](test-coverage-review.md).


## Candidate SCM pipeline — KAN-29

The separate job ai-modernization-candidate now loads candidate/cargotracker/Jenkinsfile from public GitHub main. Build 3 passed revision 92ebf5e169d775acd8756fe6854d0eab68972a2f, ran setup/security/harness gates and Maven domain tests, verified required outputs, and archived/fingerprinted the WAR, security JAR, six JUnit XML reports and revision file. SCM polling H/15 * * * * is installed in the job configuration. The historical ai-modernization-baseline job/node/controller executor settings were preserved. The candidate agent image runs Java 25.0.5/Maven 3.10.0/Python 3.14.4/Git 2.53.0 without a Docker socket.

Builds 1 and 2 failed before a successful run: the first attempted a test requiring the ignored legacy source tree; the second exposed Groovy interpolation in the shell loop. Both were corrected and independently reviewed. Build 3 is successful. The Declarative linter endpoint returned HTTP 403 to anonymous access; the successful build is the installed integration validation. Full evidence and artifact hashes are in [KAN-29 evidence](evidence/kan-29-jenkins-candidate/summary.json).

The candidate agent has been stopped while its inbound connection secret is rotated through authenticated Jenkins administration. Do not restart the agent until that is complete.
