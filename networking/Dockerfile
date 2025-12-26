# Build stage
FROM maven:3.8.4-openjdk-17-slim AS builder

WORKDIR /app

# Copy pom and source
COPY pom.xml .
RUN mvn dependency:go-offline

COPY src ./src

# Build the application
RUN mvn clean package -DskipTests

# Final stage
FROM openjdk:17-slim

WORKDIR /app

# Copy the jar
COPY --from=builder /app/target/*.jar app.jar

# Expose port
EXPOSE 8080

# Run the application
CMD ["java", "-jar", "app.jar"]
