#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include "logger.h"

extern RingBuffer* ring_buffer_create(uint32_t capacity);
extern void ring_buffer_destroy(RingBuffer* rb);
extern bool ring_buffer_push(RingBuffer* rb, const LogEntry* entry);
extern bool ring_buffer_pop(RingBuffer* rb, LogEntry* entry);
extern void metrics_init();
extern void metrics_add_log(LogLevel level, size_t size);
extern void metrics_report();

static RingBuffer* g_rb = NULL;
static pthread_t g_consumer_thread;
static _Atomic bool g_running = false;

static const char* level_to_str(LogLevel level) {
    switch (level) {
        case LOG_LEVEL_DEBUG: return "DEBUG";
        case LOG_LEVEL_INFO:  return "INFO";
        case LOG_LEVEL_WARN:  return "WARN";
        case LOG_LEVEL_ERROR: return "ERROR";
        case LOG_LEVEL_CRITICAL: return "CRITICAL";
        default: return "UNKNOWN";
    }
}

void* log_consumer(void* arg) {
    LogEntry entry;
    while (atomic_load(&g_running)) {
        if (ring_buffer_pop(g_rb, &entry)) {
            printf("[%llu] %s [%s]: %s\n", 
                   entry.timestamp, 
                   level_to_str(entry.level), 
                   entry.source, 
                   entry.message);
            metrics_add_log(entry.level, strlen(entry.message));
        } else {
            usleep(1000); // 1ms sleep if empty
        }
    }
    return NULL;
}

bool logger_init() {
    g_rb = ring_buffer_create(LOG_BUFFER_CAPACITY);
    if (!g_rb) return false;

    metrics_init();
    atomic_store(&g_running, true);
    
    if (pthread_create(&g_consumer_thread, NULL, log_consumer, NULL) != 0) {
        atomic_store(&g_running, false);
        ring_buffer_destroy(g_rb);
        return false;
    }

    return true;
}

void logger_shutdown() {
    atomic_store(&g_running, false);
    pthread_join(g_consumer_thread, NULL);
    
    // Flush remaining
    LogEntry entry;
    while (ring_buffer_pop(g_rb, &entry)) {
        printf("[EXIT FLUSH] [%llu] %s [%s]: %s\n", 
               entry.timestamp, 
               level_to_str(entry.level), 
               entry.source, 
               entry.message);
    }

    metrics_report();
    ring_buffer_destroy(g_rb);
}

void logger_log(LogLevel level, const char* source, const char* format, ...) {
    LogEntry entry;
    entry.level = level;
    strncpy(entry.source, source, sizeof(entry.source) - 1);
    entry.timestamp = (uint64_t)time(NULL);

    va_list args;
    va_start(args, format);
    vsnprintf(entry.message, MAX_LOG_MESSAGE_SIZE, format, args);
    va_end(args);

    if (!ring_buffer_push(g_rb, &entry)) {
        // Buffer full - direct print for critical logs
        if (level >= LOG_LEVEL_WARN) {
            fprintf(stderr, "[OVERFLOW] [%llu] %s [%s]: %s\n", 
                    entry.timestamp, level_to_str(level), source, entry.message);
        }
    }
}

int main() {
    if (!logger_init()) {
        fprintf(stderr, "Failed to initialize logger\n");
        return 1;
    }

    logger_log(LOG_LEVEL_INFO, "SYSTEM", "Sentinel Logging Engine initialized. Performance mode active.");
    
    // Simulation loop
    for (int i = 0; i < 100; i++) {
        logger_log(LOG_LEVEL_DEBUG, "CORE", "Heartbeat event captured. Seq: %d", i);
        if (i % 10 == 0) {
            logger_log(LOG_LEVEL_INFO, "STATS", "Processing batch %d...", i/10);
        }
        usleep(100000); // 100ms
    }

    logger_shutdown();
    return 0;
}
