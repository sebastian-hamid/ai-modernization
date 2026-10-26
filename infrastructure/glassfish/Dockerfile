FROM maven@sha256:b9fac8295f9d342af5d815888dca1334b12833a84c870c260b88f31285c1ef3d
COPY unpacked/glassfish4 /opt/glassfish4
COPY patches/bean-validator.jar /opt/glassfish4/glassfish/modules/bean-validator.jar
COPY cargo-tracker.war /opt/cargo-tracker.war
COPY start.sh /opt/start.sh
RUN chmod +x /opt/glassfish4/bin/* /opt/glassfish4/glassfish/bin/* /opt/start.sh && chown -R 1000:1000 /opt/glassfish4 /opt/cargo-tracker.war
ENV HOME=/tmp
USER 1000:1000
EXPOSE 8080
CMD ["/bin/bash","/opt/start.sh"]
