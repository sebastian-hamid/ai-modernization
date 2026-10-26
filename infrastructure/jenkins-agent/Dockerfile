FROM jenkins/inbound-agent@sha256:c93e68c1b1a9e5c4cb8e459dfd0f7fc63b6dc86b47f12883b8231c85d2e4ca4d AS remoting
FROM maven@sha256:b9fac8295f9d342af5d815888dca1334b12833a84c870c260b88f31285c1ef3d
USER root
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
COPY --from=remoting /opt/java/openjdk /opt/java21
COPY --from=remoting /usr/share/jenkins/agent.jar /usr/share/jenkins/agent.jar
COPY start.sh /usr/local/bin/start-lab-agent
RUN mkdir -p /home/jenkins/agent && chown -R 1000:1000 /home/jenkins && chmod +x /usr/local/bin/start-lab-agent
ENV HOME=/home/jenkins
USER 1000:1000
WORKDIR /home/jenkins/agent
ENTRYPOINT ["/usr/local/bin/start-lab-agent"]
