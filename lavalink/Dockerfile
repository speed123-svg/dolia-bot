FROM eclipse-temurin:17-jre

WORKDIR /opt/lavalink

ENV JAVA_TOOL_OPTIONS="-Xms128m -Xmx384m -XX:+UseG1GC -XX:+ExitOnOutOfMemoryError -Djava.awt.headless=true"

COPY lavalink/Lavalink.jar ./Lavalink.jar
COPY lavalink/application.yml ./application.yml
COPY lavalink/plugins ./plugins

EXPOSE 2333

CMD ["java", "-jar", "Lavalink.jar"]
