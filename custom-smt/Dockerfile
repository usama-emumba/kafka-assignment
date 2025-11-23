FROM maven:3.8-openjdk-11 AS builder

WORKDIR /build
COPY pom.xml .
COPY src ./src

# Build the JAR
RUN mvn clean package

# Use alpine for minimal final image
FROM alpine:latest
WORKDIR /output
COPY --from=builder /build/target/pii-field-remover-1.0.0-jar-with-dependencies.jar .

CMD ["cp", "/output/pii-field-remover-1.0.0-jar-with-dependencies.jar", "/target/"]
