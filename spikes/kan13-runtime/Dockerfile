FROM maven@sha256:9d329e21adce7c0cc53f2fd21e73c127a247c73287b8503196136ec5cff52328 AS build
WORKDIR /build
COPY pom.xml .
COPY src src
RUN java -version && mvn -version && mvn -B -ntp package
FROM quay.io/wildfly/wildfly@sha256:3fc71f6c4fe1075ac942dbb652799840ecd5424458def6039f829bf3221a8daf
# Official WildFly base currently includes 25.0.4.1; use the pinned current JDK 25.0.5.
# The assembled runtime is tested by this spike; no EE-on-Java-25 TCK claim is made.
COPY --from=build /opt/java/openjdk /opt/java/openjdk
COPY --from=build --chown=jboss:root /build/target/kan13-runtime.war /opt/jboss/wildfly/standalone/deployments/
COPY --chown=jboss:root start.sh /opt/jboss/start-kan13.sh
RUN java -version && chmod 750 /opt/jboss/start-kan13.sh
CMD ["/opt/jboss/start-kan13.sh"]

