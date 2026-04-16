FROM eclipse-temurin:17-jre

WORKDIR /opt/lavalink

COPY lavalink/Lavalink.jar ./Lavalink.jar
COPY lavalink/application.yml ./application.yml
COPY lavalink/plugins ./plugins

EXPOSE 2333

CMD ["java", "-jar", "Lavalink.jar"]
