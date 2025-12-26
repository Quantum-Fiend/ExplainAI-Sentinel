FROM gcc:latest AS builder

WORKDIR /app

# Copy source code
COPY . .

# Build the logger (static binary for portability)
RUN gcc -O3 -o logger src/logger.c src/ring_buffer.c src/metrics.c -Iinclude -lpthread

FROM alpine:latest

WORKDIR /app

# Install dependencies for running
RUN apk add --no-cache libc6-compat

# Copy the binary
COPY --from=builder /app/logger .

# Run the application
CMD ["./logger"]
