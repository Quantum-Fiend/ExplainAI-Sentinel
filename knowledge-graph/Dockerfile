# Build stage
FROM hseeberger/scala-sbt:17.0.2_1.6.2_2.13.8 AS builder

WORKDIR /app

# Copy build definition
COPY build.sbt .
COPY project ./project

# Fetch dependencies
RUN sbt update

# Copy source code
COPY src ./src

# Build the assembly jar
RUN sbt assembly

# Final stage
FROM openjdk:17-slim

WORKDIR /app

# Copy the jar
COPY --from=builder /app/target/scala-2.13/*.jar app.jar

# Expose port
EXPOSE 8002

# Run the application
CMD ["java", "-jar", "app.jar"]
