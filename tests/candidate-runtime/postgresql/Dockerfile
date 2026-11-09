FROM maven@sha256:9d329e21adce7c0cc53f2fd21e73c127a247c73287b8503196136ec5cff52328 AS build
WORKDIR /build/library
COPY candidate/security/pom.xml .
COPY candidate/security/src src
RUN mvn -B -ntp install
WORKDIR /build/candidate
COPY candidate/cargotracker/pom.xml .
COPY candidate/cargotracker/src src
RUN mvn -B -ntp package -Dsession.timeout.minutes=1
FROM quay.io/wildfly/wildfly@sha256:3fc71f6c4fe1075ac942dbb652799840ecd5424458def6039f829bf3221a8daf
COPY --from=build /opt/java/openjdk /opt/java/openjdk
COPY --from=build /build/candidate/target/cargo-tracker.war /opt/jboss/wildfly/standalone/deployments/
USER root
RUN mkdir -p /opt/jboss/wildfly/modules/org/postgresql/main
ADD https://repo.maven.apache.org/maven2/org/postgresql/postgresql/42.7.14/postgresql-42.7.14.jar /opt/jboss/wildfly/modules/org/postgresql/main/postgresql-42.7.14.jar
RUN echo "73914527305a40cce504b0d3d90b23caf565136912d607ae8ae7c5895512332c  /opt/jboss/wildfly/modules/org/postgresql/main/postgresql-42.7.14.jar" | sha256sum -c -
COPY tests/candidate-runtime/postgresql/module.xml /opt/jboss/wildfly/modules/org/postgresql/main/module.xml
COPY tests/candidate-runtime/postgresql/configure-datasource.cli /opt/jboss/configure-postgresql-datasource.cli
COPY tests/candidate-runtime/postgresql/start.sh /opt/jboss/start-postgresql-candidate.sh
RUN chown -R jboss:root /opt/jboss/wildfly/modules/org/postgresql /opt/jboss/configure-postgresql-datasource.cli /opt/jboss/start-postgresql-candidate.sh && chmod 750 /opt/jboss/start-postgresql-candidate.sh
USER jboss
CMD ["/opt/jboss/start-postgresql-candidate.sh"]
