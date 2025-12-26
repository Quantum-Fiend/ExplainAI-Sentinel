#include <stdio.h>
#include <time.h>
#include "logger.h"

static Metrics g_metrics;

void metrics_init() {
    atomic_init(&g_metrics.total_logs, 0);
    atomic_init(&g_metrics.error_logs, 0);
    atomic_init(&g_metrics.bytes_processed, 0);
    g_metrics.start_time = time(NULL);
}

void metrics_add_log(LogLevel level, size_t size) {
    atomic_fetch_add_explicit(&g_metrics.total_logs, 1, memory_order_relaxed);
    if (level >= LOG_LEVEL_ERROR) {
        atomic_fetch_add_explicit(&g_metrics.error_logs, 1, memory_order_relaxed);
    }
    atomic_fetch_add_explicit(&g_metrics.bytes_processed, size, memory_order_relaxed);
}

void metrics_report() {
    uint64_t total = atomic_load_explicit(&g_metrics.total_logs, memory_order_relaxed);
    uint64_t errors = atomic_load_explicit(&g_metrics.error_logs, memory_order_relaxed);
    uint64_t bytes = atomic_load_explicit(&g_metrics.bytes_processed, memory_order_relaxed);
    uint64_t duration = time(NULL) - g_metrics.start_time;

    printf("\n=== Sentinel Logging Metrics ===\n");
    printf("Uptime: %llu seconds\n", duration);
    printf("Total Logs: %llu\n", total);
    printf("Error Logs: %llu\n", errors);
    printf("Data Processed: %llu bytes\n", bytes);
    if (duration > 0) {
        printf("Throughput: %.2f logs/sec\n", (double)total / duration);
    }
    printf("===============================\n\n");
}
