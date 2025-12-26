#ifndef SENTINEL_LOGGER_H
#define SENTINEL_LOGGER_H

#include <stdint.h>
#include <stdbool.h>
#include <time.h>

#define MAX_LOG_MESSAGE_SIZE 1024
#define LOG_BUFFER_CAPACITY (1024 * 16)

typedef enum {
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_INFO,
    LOG_LEVEL_WARN,
    LOG_LEVEL_ERROR,
    LOG_LEVEL_CRITICAL
} LogLevel;

typedef struct {
    LogLevel level;
    char message[MAX_LOG_MESSAGE_SIZE];
    uint64_t timestamp;
    char source[64];
} LogEntry;

// Ring Buffer Structure
typedef struct {
    LogEntry* entries;
    uint32_t capacity;
    _Atomic uint32_t head;
    _Atomic uint32_t tail;
} RingBuffer;

// Metrics Structure
typedef struct {
    _Atomic uint64_t total_logs;
    _Atomic uint64_t error_logs;
    _Atomic uint64_t bytes_processed;
    uint64_t start_time;
} Metrics;

// Function declarations
bool logger_init();
void logger_shutdown();
void logger_log(LogLevel level, const char* source, const char* format, ...);
void logger_flush();

// Metrics functions
void metrics_init();
void metrics_report();

#endif // SENTINEL_LOGGER_H
