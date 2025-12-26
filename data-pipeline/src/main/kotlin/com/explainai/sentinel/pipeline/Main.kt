package com.explainai.sentinel.pipeline

import com.explainai.sentinel.pipeline.stream.SecurityEventStreamProcessor
import com.explainai.sentinel.pipeline.etl.ETLPipeline
import kotlinx.coroutines.runBlocking
import mu.KotlinLogging

private val logger = KotlinLogging.logger {}

fun main(args: Array<String>) {
    logger.info { "Starting ExplainAI-Sentinel Data Pipeline" }

    when (args.getOrNull(0)) {
        "stream" -> startStreamProcessor()
        "etl" -> runETLPipeline()
        else -> {
            println("Usage: data-pipeline [stream|etl]")
            println("  stream - Start Kafka Streams processor")
            println("  etl    - Run ETL pipeline")
        }
    }
}

fun startStreamProcessor() {
    logger.info { "Starting stream processor..." }
    
    val processor = SecurityEventStreamProcessor(
        bootstrapServers = System.getenv("KAFKA_BOOTSTRAP_SERVERS") ?: "localhost:9092"
    )
    
    processor.start()
    
    // Keep running
    Thread.currentThread().join()
}

fun runETLPipeline() = runBlocking {
    logger.info { "Running ETL pipeline..." }
    
    val pipeline = ETLPipeline()
    
    // Example pipeline configuration
    val config = com.explainai.sentinel.pipeline.etl.PipelineConfig(
        name = "security-events-import",
        source = com.explainai.sentinel.pipeline.etl.DataSource(
            type = com.explainai.sentinel.pipeline.etl.SourceType.CSV,
            location = "data/events.csv"
        ),
        transformations = listOf(
            com.explainai.sentinel.pipeline.etl.Transformation(
                type = com.explainai.sentinel.pipeline.etl.TransformationType.ENRICH,
                params = emptyList()
            )
        ),
        destination = com.explainai.sentinel.pipeline.etl.DataDestination(
            type = com.explainai.sentinel.pipeline.etl.DestinationType.KAFKA,
            location = "security-events-raw"
        )
    )
    
    val result = pipeline.runPipeline(config)
    
    logger.info { "Pipeline completed: $result" }
}
