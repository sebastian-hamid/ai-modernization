FROM maven@sha256:84bd96155bf37d1be2858433aee89320f487c2d21faf06406640e7dc2b82d686 AS build
WORKDIR /build/library
COPY candidate/security/pom.xml .
COPY candidate/security/src src
RUN mvn -B -ntp install
WORKDIR /build/fixture
COPY tests/security-runtime/pom.xml .
COPY tests/security-runtime/src src
RUN mvn -B -ntp package
FROM quay.io/wildfly/wildfly@sha256:3fc71f6c4fe1075ac942dbb652799840ecd5424458def6039f829bf3221a8daf
# Official WildFly base currently includes 25.0.4.1; use patched Temurin JDK 25.0.5.1+2 from the refreshed Maven image.
# The assembled runtime is tested by this spike; no EE-on-Java-25 TCK claim is made.
COPY --from=build /opt/java/openjdk /opt/java/openjdk
COPY --from=build --chown=jboss:root /build/fixture/target/security-fixture.war /opt/jboss/wildfly/standalone/deployments/
COPY --chown=jboss:root tests/security-runtime/start.sh /opt/jboss/start-kan15.sh
RUN java -version && chmod 750 /opt/jboss/start-kan15.sh
CMD ["/opt/jboss/start-kan15.sh"]
