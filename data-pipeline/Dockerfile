# Build stage
FROM gradle:8.5-jdk17 AS builder

WORKDIR /app

# Copy gradle files
COPY build.gradle.kts settings.gradle.kts ./
RUN gradle build -x test --continue

# Copy source code
COPY . .

# Build the application
RUN gradle build -x test

# Final stage
FROM openjdk:17-slim

WORKDIR /app

# Copy the fat jar
COPY --from=builder /app/build/libs/*.jar app.jar

# Run the application
CMD ["java", "-jar", "app.jar"]
