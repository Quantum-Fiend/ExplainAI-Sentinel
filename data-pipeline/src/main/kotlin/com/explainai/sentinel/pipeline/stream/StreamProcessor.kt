package com.explainai.sentinel.pipeline.stream

import com.explainai.sentinel.pipeline.model.*
import kotlinx.serialization.json.Json
import kotlinx.serialization.encodeToString
import kotlinx.serialization.decodeFromString
import mu.KotlinLogging
import org.apache.kafka.common.serialization.Serdes
import org.apache.kafka.streams.KafkaStreams
import org.apache.kafka.streams.StreamsBuilder
import org.apache.kafka.streams.StreamsConfig
import org.apache.kafka.streams.kstream.*
import java.time.Duration
import java.util.*

private val logger = KotlinLogging.logger {}

class SecurityEventStreamProcessor(
    private val bootstrapServers: String = "localhost:9092",
    private val applicationId: String = "sentinel-stream-processor"
) {
    
    private val json = Json { ignoreUnknownKeys = true }
    private lateinit var streams: KafkaStreams

    fun start() {
        val props = Properties().apply {
            put(StreamsConfig.APPLICATION_ID_CONFIG, applicationId)
            put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers)
            put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String()::class.java)
            put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String()::class.java)
        }

        val builder = StreamsBuilder()
        buildTopology(builder)

        streams = KafkaStreams(builder.build(), props)
        streams.start()

        logger.info { "Security Event Stream Processor started" }

        // Shutdown hook
        Runtime.getRuntime().addShutdownHook(Thread {
            streams.close()
            logger.info { "Stream processor stopped" }
        })
    }

    private fun buildTopology(builder: StreamsBuilder) {
        // Input stream
        val rawEvents: KStream<String, String> = builder.stream("security-events-raw")

        // Parse and validate
        val validEvents = rawEvents
            .mapValues { value -> parseEvent(value) }
            .filter { _, event -> event != null }
            .mapValues { event -> event!! }

        // Branch by severity
        val branches = validEvents.split(
            Named.`as`("severity-split")
        ) { _, event ->
            when (event.severity) {
                Severity.CRITICAL, Severity.HIGH -> 0
                Severity.MEDIUM -> 1
                else -> 2
            }
        }

        // High priority events - immediate processing
        branches[0]
            .peek { key, event -> 
                logger.warn { "High priority event: ${event.eventId}" }
            }
            .to("security-events-high-priority")

        // Medium priority - enrichment
        branches[1]
            .mapValues { event -> enrichEvent(event) }
            .to("security-events-enriched")

        // Low priority - batch processing
        branches[2]
            .to("security-events-batch")

        // Aggregations
        buildAggregations(validEvents)

        // Anomaly detection stream
        buildAnomalyDetection(validEvents)
    }

    private fun buildAggregations(events: KStream<String, SecurityEvent>) {
        // Count by severity in 5-minute windows
        events
            .groupBy(
                { _, event -> event.severity.name },
                Grouped.with(Serdes.String(), Serdes.String())
            )
            .windowedBy(TimeWindows.ofSizeWithNoGrace(Duration.ofMinutes(5)))
            .count(Materialized.`as`("severity-counts"))
            .toStream()
            .map { windowedKey, count ->
                val key = "${windowedKey.key()}-${windowedKey.window().start()}"
                val value = json.encodeToString(
                    mapOf(
                        "severity" to windowedKey.key(),
                        "count" to count,
                        "windowStart" to windowedKey.window().start(),
                        "windowEnd" to windowedKey.window().end()
                    )
                )
                KeyValue(key, value)
            }
            .to("security-metrics-aggregated")

        // Top sources by event count
        events
            .groupBy(
                { _, event -> event.source },
                Grouped.with(Serdes.String(), Serdes.String())
            )
            .windowedBy(TimeWindows.ofSizeWithNoGrace(Duration.ofMinutes(10)))
            .count()
            .toStream()
            .map { windowedKey, count ->
                KeyValue(
                    windowedKey.key(),
                    json.encodeToString(mapOf("source" to windowedKey.key(), "count" to count))
                )
            }
            .to("top-event-sources")
    }

    private fun buildAnomalyDetection(events: KStream<String, SecurityEvent>) {
        // Detect rapid succession of events from same source
        events
            .groupByKey()
            .windowedBy(SessionWindows.ofInactivityGapWithNoGrace(Duration.ofMinutes(1)))
            .count()
            .toStream()
            .filter { _, count -> count > 10 } // More than 10 events in 1 minute
            .map { windowedKey, count ->
                val anomaly = mapOf(
                    "type" to "rapid_succession",
                    "source" to windowedKey.key(),
                    "eventCount" to count,
                    "windowStart" to windowedKey.window().start(),
                    "windowEnd" to windowedKey.window().end()
                )
                KeyValue(windowedKey.key(), json.encodeToString(anomaly))
            }
            .to("security-anomalies")
    }

    private fun parseEvent(value: String): SecurityEvent? {
        return try {
            json.decodeFromString<SecurityEvent>(value)
        } catch (e: Exception) {
            logger.error(e) { "Failed to parse event: $value" }
            null
        }
    }

    private fun enrichEvent(event: SecurityEvent): String {
        val enriched = EnrichedEvent(
            event = event,
            enrichments = mapOf(
                "processed_by" to "kotlin-stream-processor",
                "enrichment_timestamp" to System.currentTimeMillis()
            ),
            geoLocation = lookupGeoLocation(event),
            threatIntelligence = lookupThreatIntel(event)
        )
        return json.encodeToString(enriched)
    }

    private fun lookupGeoLocation(event: SecurityEvent): GeoLocation? {
        // Placeholder - integrate with GeoIP service
        val ip = event.attributes["source_ip"] ?: return null
        return GeoLocation(
            country = "US",
            city = "San Francisco",
            latitude = 37.7749,
            longitude = -122.4194
        )
    }

    private fun lookupThreatIntel(event: SecurityEvent): ThreatInfo? {
        // Placeholder - integrate with threat intelligence API
        return ThreatInfo(
            isMalicious = false,
            threatLevel = "low",
            categories = listOf("benign"),
            confidence = 0.95
        )
    }

    fun stop() {
        if (::streams.isInitialized) {
            streams.close()
        }
    }
}
