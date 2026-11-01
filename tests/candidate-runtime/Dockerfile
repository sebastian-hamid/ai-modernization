FROM maven@sha256:9d329e21adce7c0cc53f2fd21e73c127a247c73287b8503196136ec5cff52328 AS build
WORKDIR /build/library
COPY candidate/security/pom.xml .
COPY candidate/security/src src
RUN mvn -B -ntp install
WORKDIR /build/candidate
COPY candidate/cargotracker/pom.xml .
COPY candidate/cargotracker/src src
# Lab-only descriptor replaces safe default only in this disposable fixture image.
COPY tests/candidate-runtime/persistence-lab.xml src/main/resources/META-INF/persistence.xml
# Observer and interceptor exist only in this opt-in disposable fixture, never candidate source.
COPY tests/candidate-runtime/observer/*.java /tmp/observer/
COPY tests/candidate-runtime/observer/ejb-jar.xml src/main/webapp/WEB-INF/ejb-jar.xml
RUN mkdir -p src/main/java/lab/fixture && cp /tmp/observer/LabEffects*.java /tmp/observer/InvocationAudit.java /tmp/observer/RoutingIdentityFilter.java src/main/java/lab/fixture/
RUN mvn -B -ntp package -Dsession.timeout.minutes=1
RUN mkdir /tmp/observer-client && javac -d /tmp/observer-client /tmp/observer/ReadEffects.java
FROM quay.io/wildfly/wildfly@sha256:3fc71f6c4fe1075ac942dbb652799840ecd5424458def6039f829bf3221a8daf
# Official WildFly base currently includes 25.0.4.1; use the pinned current JDK 25.0.5.
# The assembled runtime is tested by this spike; no EE-on-Java-25 TCK claim is made.
COPY --from=build /opt/java/openjdk /opt/java/openjdk
COPY --from=build /build/candidate/target/surefire-reports /opt/jboss/lab-evidence/surefire
COPY --from=build --chown=jboss:root /build/candidate/target/cargo-tracker.war /opt/jboss/wildfly/standalone/deployments/
COPY --chown=jboss:root tests/candidate-runtime/start.sh /opt/jboss/start-kan18.sh
COPY --from=build /tmp/observer-client /opt/jboss/observer-client
RUN java -version && chmod 750 /opt/jboss/start-kan18.sh
CMD ["/opt/jboss/start-kan18.sh"]
