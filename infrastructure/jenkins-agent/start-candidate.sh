#!/usr/bin/env bash
set -euo pipefail
secret="$(cat /run/secrets/jenkins-agent)"
exec /opt/java21/bin/java -jar /usr/share/jenkins/agent.jar \
  -url http://ai-modernization-jenkins:8080/ \
  -name ai-modernization-candidate-secure \
  -secret "$secret" -webSocket -workDir /home/jenkins/agent
