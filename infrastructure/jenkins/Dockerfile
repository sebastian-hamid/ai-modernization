ARG JENKINS_BASE=jenkins/jenkins:2.580.1-lts-jdk21@sha256:a660310e39ade10631f774bacd5219de767dfd08947ea5c32a739b5e5bb382c1
ARG PATCHED_JDK=eclipse-temurin:21.0.13.1_2-jdk-jammy@sha256:4b3d0998ee65462bd86ff060c87119b3575294cb3d0927372afa6f3708b0c8db

FROM ${PATCHED_JDK} AS patched-jdk
FROM ${JENKINS_BASE}
USER root
COPY --from=patched-jdk /opt/java/openjdk/ /opt/java/openjdk/
RUN chown -R jenkins:jenkins /opt/java/openjdk && java -version
USER jenkins
