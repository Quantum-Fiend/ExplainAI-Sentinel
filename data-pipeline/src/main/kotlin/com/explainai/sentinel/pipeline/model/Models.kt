package com.explainai.sentinel.pipeline.model

import kotlinx.serialization.Serializable
import java.time.Instant

@Serializable
data class SecurityEvent(
    val eventId: String,
    val timestamp: Long = Instant.now().toEpochMilli(),
    val eventType: String,
    val source: String,
    val severity: Severity,
    val attributes: Map<String, String> = emptyMap(),
    val metadata: Map<String, String> = emptyMap()
)

@Serializable
enum class Severity {
    CRITICAL, HIGH, MEDIUM, LOW, INFO
}

@Serializable
data class EnrichedEvent(
    val event: SecurityEvent,
    val enrichments: Map<String, Any>,
    val geoLocation: GeoLocation? = null,
    val threatIntelligence: ThreatInfo? = null,
    val processedAt: Long = Instant.now().toEpochMilli()
)

@Serializable
data class GeoLocation(
    val country: String,
    val city: String,
    val latitude: Double,
    val longitude: Double
)

@Serializable
data class ThreatInfo(
    val isMalicious: Boolean,
    val threatLevel: String,
    val categories: List<String>,
    val confidence: Double
)

@Serializable
data class AggregatedMetrics(
    val windowStart: Long,
    val windowEnd: Long,
    val eventCount: Long,
    val severityCounts: Map<Severity, Long>,
    val topSources: Map<String, Long>,
    val averageProcessingTime: Double
)

data class ValidationResult<T>(
    val isValid: Boolean,
    val data: T?,
    val errors: List<String> = emptyList()
)

data class TransformationContext(
    val eventId: String,
    val startTime: Long = System.currentTimeMillis(),
    val metadata: MutableMap<String, Any> = mutableMapOf()
)
