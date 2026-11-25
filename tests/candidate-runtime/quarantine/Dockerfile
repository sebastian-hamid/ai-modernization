FROM maven@sha256:84bd96155bf37d1be2858433aee89320f487c2d21faf06406640e7dc2b82d686 AS build
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
RUN mkdir -p /opt/jboss/wildfly/modules/org/postgresql/main /opt/jboss/wildfly/standalone/data/activemq && chown -R jboss:root /opt/jboss/wildfly/standalone/data
ADD https://repo.maven.apache.org/maven2/org/postgresql/postgresql/42.7.14/postgresql-42.7.14.jar /opt/jboss/wildfly/modules/org/postgresql/main/postgresql-42.7.14.jar
RUN echo "73914527305a40cce504b0d3d90b23caf565136912d607ae8ae7c5895512332c  /opt/jboss/wildfly/modules/org/postgresql/main/postgresql-42.7.14.jar" | sha256sum -c -
COPY tests/candidate-runtime/postgresql/module.xml /opt/jboss/wildfly/modules/org/postgresql/main/module.xml
COPY tests/candidate-runtime/postgresql/configure-datasource.cli /opt/jboss/configure-postgresql-datasource.cli
COPY candidate/cargotracker/deployment/wildfly/notification-disposition.cli /opt/jboss/notification-disposition.cli
COPY tests/candidate-runtime/quarantine/start.sh /opt/jboss/start-quarantine-candidate.sh
RUN chown -R jboss:root /opt/jboss/wildfly/modules/org/postgresql /opt/jboss/configure-postgresql-datasource.cli /opt/jboss/notification-disposition.cli /opt/jboss/start-quarantine-candidate.sh && chmod 750 /opt/jboss/start-quarantine-candidate.sh
USER jboss
CMD ["/opt/jboss/start-quarantine-candidate.sh"]
