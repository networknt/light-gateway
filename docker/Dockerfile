# Stage 1: Build the custom JRE
FROM amazoncorretto:25-alpine as packager

# Helpful check to verify the build version in logs
RUN { \
        java --version ; \
        echo "jlink version:" && \
        $JAVA_HOME/bin/jlink --version ; \
    }

ENV JAVA_MINIMAL=/opt/jre

# Install binutils for objcopy (required for jlink --strip-debug on Alpine)
RUN apk add --no-cache binutils

# Build modules distribution
# NOTE: Updated --compress from '2' to 'zip-9' for JDK 21+ compatibility
RUN $JAVA_HOME/bin/jlink \
    --verbose \
    --add-modules \
        java.base,java.sql,java.naming,java.desktop,java.xml,jdk.crypto.cryptoki,jdk.crypto.ec,jdk.unsupported,java.management,java.security.jgss,java.net.http \
    --compress zip-9 \
    --strip-debug \
    --no-header-files \
    --no-man-pages \
    --output "$JAVA_MINIMAL"

# Stage 2: Runtime image
FROM alpine:latest

ENV JAVA_MINIMAL=/opt/jre
ENV PATH="$PATH:$JAVA_MINIMAL/bin"

# Copy the custom JRE created in the previous stage
COPY --from=packager "$JAVA_MINIMAL" "$JAVA_MINIMAL"

# Copy the application jar (Specific to light-gateway)
COPY /target/light-gateway.jar server.jar

# Run the application
CMD ["/bin/sh","-c","exec java -Dlight-4j-config-dir=/config -Dlogback.configurationFile=/config/logback.xml -jar /server.jar"]
