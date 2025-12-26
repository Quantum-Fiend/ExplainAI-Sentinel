package com.explainai.sentinel.pipeline.etl

import com.explainai.sentinel.pipeline.model.*
import com.github.doyaaaaaken.kotlincsv.dsl.csvReader
import kotlinx.coroutines.*
import kotlinx.serialization.json.Json
import mu.KotlinLogging
import java.io.File
import java.time.Instant

private val logger = KotlinLogging.logger {}

class ETLPipeline {
    
    private val json = Json { prettyPrint = true }

    /**
     * Extract data from various sources
     */
    suspend fun extract(source: DataSource): List<Map<String, String>> = coroutineScope {
        logger.info { "Extracting data from ${source.type}" }
        
        when (source.type) {
            SourceType.CSV -> extractFromCSV(source.location)
            SourceType.JSON -> extractFromJSON(source.location)
            SourceType.DATABASE -> extractFromDatabase(source.location)
            SourceType.API -> extractFromAPI(source.location)
        }
    }

    /**
     * Transform raw data into security events
     */
    suspend fun transform(
        rawData: List<Map<String, String>>,
        transformations: List<Transformation>
    ): List<SecurityEvent> = coroutineScope {
        logger.info { "Transforming ${rawData.size} records" }
        
        rawData.mapNotNull { record ->
            try {
                var transformed = record
                
                // Apply transformations
                transformations.forEach { transformation ->
                    transformed = applyTransformation(transformed, transformation)
                }
                
                // Convert to SecurityEvent
                mapToSecurityEvent(transformed)
            } catch (e: Exception) {
                logger.error(e) { "Failed to transform record: $record" }
                null
            }
        }
    }

    /**
     * Load transformed data to destination
     */
    suspend fun load(
        events: List<SecurityEvent>,
        destination: DataDestination
    ): LoadResult = coroutineScope {
        logger.info { "Loading ${events.size} events to ${destination.type}" }
        
        try {
            when (destination.type) {
                DestinationType.KAFKA -> loadToKafka(events, destination.location)
                DestinationType.DATABASE -> loadToDatabase(events, destination.location)
                DestinationType.FILE -> loadToFile(events, destination.location)
            }
            
            LoadResult(
                success = true,
                recordsProcessed = events.size,
                recordsFailed = 0,
                errors = emptyList()
            )
        } catch (e: Exception) {
            logger.error(e) { "Failed to load data" }
            LoadResult(
                success = false,
                recordsProcessed = 0,
                recordsFailed = events.size,
                errors = listOf(e.message ?: "Unknown error")
            )
        }
    }

    /**
     * Run complete ETL pipeline
     */
    suspend fun runPipeline(config: PipelineConfig): PipelineResult = coroutineScope {
        val startTime = System.currentTimeMillis()
        logger.info { "Starting ETL pipeline: ${config.name}" }
        
        try {
            // Extract
            val rawData = extract(config.source)
            logger.info { "Extracted ${rawData.size} records" }
            
            // Transform
            val events = transform(rawData, config.transformations)
            logger.info { "Transformed to ${events.size} events" }
            
            // Validate
            val validEvents = events.filter { validateEvent(it).isValid }
            logger.info { "Validated ${validEvents.size} events" }
            
            // Load
            val loadResult = load(validEvents, config.destination)
            
            val duration = System.currentTimeMillis() - startTime
            
            PipelineResult(
                success = loadResult.success,
                recordsExtracted = rawData.size,
                recordsTransformed = events.size,
                recordsLoaded = validEvents.size,
                durationMs = duration,
                errors = loadResult.errors
            )
        } catch (e: Exception) {
            logger.error(e) { "Pipeline failed" }
            PipelineResult(
                success = false,
                recordsExtracted = 0,
                recordsTransformed = 0,
                recordsLoaded = 0,
                durationMs = System.currentTimeMillis() - startTime,
                errors = listOf(e.message ?: "Unknown error")
            )
        }
    }

    // Private helper methods

    private fun extractFromCSV(location: String): List<Map<String, String>> {
        return csvReader().readAllWithHeader(File(location))
    }

    private fun extractFromJSON(location: String): List<Map<String, String>> {
        val content = File(location).readText()
        return json.decodeFromString(content)
    }

    private suspend fun extractFromDatabase(location: String): List<Map<String, String>> {
        // Placeholder - implement database extraction
        return emptyList()
    }

    private suspend fun extractFromAPI(location: String): List<Map<String, String>> {
        // Placeholder - implement API extraction
        return emptyList()
    }

    private fun applyTransformation(
        record: Map<String, String>,
        transformation: Transformation
    ): Map<String, String> {
        return when (transformation.type) {
            TransformationType.RENAME -> {
                val (from, to) = transformation.params
                record.mapKeys { if (it.key == from) to else it.key }
            }
            TransformationType.FILTER -> {
                val field = transformation.params[0]
                val value = transformation.params[1]
                if (record[field] == value) record else emptyMap()
            }
            TransformationType.MAP -> {
                val field = transformation.params[0]
                val mapping = transformation.params[1]
                record.mapValues { 
                    if (it.key == field) mapping else it.value 
                }
            }
            TransformationType.ENRICH -> {
                record + ("enriched_at" to Instant.now().toString())
            }
        }
    }

    private fun mapToSecurityEvent(record: Map<String, String>): SecurityEvent {
        return SecurityEvent(
            eventId = record["event_id"] ?: java.util.UUID.randomUUID().toString(),
            eventType = record["event_type"] ?: "unknown",
            source = record["source"] ?: "unknown",
            severity = Severity.valueOf(record["severity"]?.uppercase() ?: "INFO"),
            attributes = record.filterKeys { it !in setOf("event_id", "event_type", "source", "severity") }
        )
    }

    private fun validateEvent(event: SecurityEvent): ValidationResult<SecurityEvent> {
        val errors = mutableListOf<String>()
        
        if (event.eventId.isBlank()) errors.add("Event ID is required")
        if (event.eventType.isBlank()) errors.add("Event type is required")
        if (event.source.isBlank()) errors.add("Source is required")
        
        return ValidationResult(
            isValid = errors.isEmpty(),
            data = if (errors.isEmpty()) event else null,
            errors = errors
        )
    }

    private suspend fun loadToKafka(events: List<SecurityEvent>, topic: String) {
        // Placeholder - implement Kafka producer
        logger.info { "Loading ${events.size} events to Kafka topic: $topic" }
    }

    private suspend fun loadToDatabase(events: List<SecurityEvent>, connectionString: String) {
        // Placeholder - implement database insertion
        logger.info { "Loading ${events.size} events to database" }
    }

    private suspend fun loadToFile(events: List<SecurityEvent>, filePath: String) {
        val file = File(filePath)
        file.writeText(json.encodeToString(events))
        logger.info { "Loaded ${events.size} events to file: $filePath" }
    }
}

// Configuration models

data class DataSource(
    val type: SourceType,
    val location: String
)

enum class SourceType {
    CSV, JSON, DATABASE, API
}

data class DataDestination(
    val type: DestinationType,
    val location: String
)

enum class DestinationType {
    KAFKA, DATABASE, FILE
}

data class Transformation(
    val type: TransformationType,
    val params: List<String>
)

enum class TransformationType {
    RENAME, FILTER, MAP, ENRICH
}

data class PipelineConfig(
    val name: String,
    val source: DataSource,
    val transformations: List<Transformation>,
    val destination: DataDestination
)

data class LoadResult(
    val success: Boolean,
    val recordsProcessed: Int,
    val recordsFailed: Int,
    val errors: List<String>
)

data class PipelineResult(
    val success: Boolean,
    val recordsExtracted: Int,
    val recordsTransformed: Int,
    val recordsLoaded: Int,
    val durationMs: Long,
    val errors: List<String>
)
