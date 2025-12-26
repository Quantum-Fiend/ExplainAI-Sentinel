#include <stdlib.h>
#include <stdatomic.h>
#include <string.h>
#include "logger.h"

RingBuffer* ring_buffer_create(uint32_t capacity) {
    RingBuffer* rb = (RingBuffer*)malloc(sizeof(RingBuffer));
    if (!rb) return NULL;

    rb->entries = (LogEntry*)malloc(sizeof(LogEntry) * capacity);
    if (!rb->entries) {
        free(rb);
        return NULL;
    }

    rb->capacity = capacity;
    atomic_init(&rb->head, 0);
    atomic_init(&rb->tail, 0);

    return rb;
}

void ring_buffer_destroy(RingBuffer* rb) {
    if (rb) {
        free(rb->entries);
        free(rb);
    }
}

bool ring_buffer_push(RingBuffer* rb, const LogEntry* entry) {
    uint32_t head = atomic_load_explicit(&rb->head, memory_order_relaxed);
    uint32_t next_head = (head + 1) % rb->capacity;

    if (next_head == atomic_load_explicit(&rb->tail, memory_order_acquire)) {
        // Buffer full
        return false;
    }

    rb->entries[head] = *entry;
    atomic_store_explicit(&rb->head, next_head, memory_order_release);
    return true;
}

bool ring_buffer_pop(RingBuffer* rb, LogEntry* entry) {
    uint32_t tail = atomic_load_explicit(&rb->tail, memory_order_relaxed);

    if (tail == atomic_load_explicit(&rb->head, memory_order_acquire)) {
        // Buffer empty
        return false;
    }

    *entry = rb->entries[tail];
    atomic_store_explicit(&rb->tail, (tail + 1) % rb->capacity, memory_order_release);
    return true;
}
