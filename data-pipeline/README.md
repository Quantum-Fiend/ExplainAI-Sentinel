# Data Transformation Pipeline

Kotlin-based data transformation and streaming pipeline for ExplainAI-Sentinel.

## Features

- **Kafka Streams Processing**: Real-time event processing
- **ETL Pipelines**: Extract, Transform, Load operations
- **Data Validation**: Schema validation and data quality checks
- **Stream Enrichment**: GeoIP lookup, threat intelligence integration
- **Aggregations**: Time-windowed metrics and analytics
- **Anomaly Detection**: Stream-based anomaly detection

## Architecture

```
data-pipeline/
├── src/main/kotlin/com/explainai/sentinel/pipeline/
│   ├── model/
│   │   └── Models.kt              # Data models
│   ├── stream/
│   │   └── StreamProcessor.kt     # Kafka Streams processor
│   ├── etl/
│   │   └── ETLPipeline.kt         # ETL operations
│   └── Main.kt                    # Entry point
└── build.gradle.kts               # Build configuration
```

## Installation

### Prerequisites

- JDK 17+
- Kotlin 1.9+
- Apache Kafka 3.6+

### Build

```bash
./gradlew build
```

## Usage

### Stream Processing Mode

Process real-time security events from Kafka:

```bash
./gradlew run --args="stream"
```

**Input Topics:**
- `security-events-raw` - Raw security events

**Output Topics:**
- `security-events-high-priority` - Critical/High severity events
- `security-events-enriched` - Enriched medium priority events
- `security-events-batch` - Low priority events for batch processing
- `security-metrics-aggregated` - Aggregated metrics
- `top-event-sources` - Top event sources
- `security-anomalies` - Detected anomalies

### ETL Mode

Run batch ETL pipeline:

```bash
./gradlew run --args="etl"
```

## Stream Processing

### Event Flow

```
Raw Events → Parse → Validate → Branch by Severity
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
                High Priority   Medium Priority  Low Priority
                    ↓               ↓               ↓
                Immediate       Enrichment       Batch
```

### Aggregations

**Severity Counts** (5-minute windows):
```kotlin
events
  .groupBy { severity }
  .windowedBy(TimeWindows.ofSizeWithNoGrace(Duration.ofMinutes(5)))
  .count()
```

**Top Sources** (10-minute windows):
```kotlin
events
  .groupBy { source }
  .windowedBy(TimeWindows.ofSizeWithNoGrace(Duration.ofMinutes(10)))
  .count()
```

### Anomaly Detection

**Rapid Succession Detection**:
- Detects >10 events from same source within 1 minute
- Uses session windows with 1-minute inactivity gap
- Outputs to `security-anomalies` topic

## ETL Pipeline

### Extract

Supported sources:
- **CSV**: Read from CSV files
- **JSON**: Parse JSON files
- **Database**: Query databases (PostgreSQL, MySQL)
- **API**: Fetch from REST APIs

### Transform

Available transformations:
- **RENAME**: Rename fields
- **FILTER**: Filter records by criteria
- **MAP**: Map values
- **ENRICH**: Add enrichment data

### Load

Supported destinations:
- **Kafka**: Produce to Kafka topics
- **Database**: Insert into databases
- **File**: Write to JSON files

### Example Pipeline

```kotlin
val config = PipelineConfig(
    name = "security-events-import",
    source = DataSource(
        type = SourceType.CSV,
        location = "data/events.csv"
    ),
    transformations = listOf(
        Transformation(
            type = TransformationType.RENAME,
            params = listOf("old_field", "new_field")
        ),
        Transformation(
            type = TransformationType.ENRICH,
            params = emptyList()
        )
    ),
    destination = DataDestination(
        type = DestinationType.KAFKA,
        location = "security-events-raw"
    )
)

val result = pipeline.runPipeline(config)
```

## Data Models

### SecurityEvent

```kotlin
data class SecurityEvent(
    val eventId: String,
    val timestamp: Long,
    val eventType: String,
    val source: String,
    val severity: Severity,
    val attributes: Map<String, String>,
    val metadata: Map<String, String>
)
```

### EnrichedEvent

```kotlin
data class EnrichedEvent(
    val event: SecurityEvent,
    val enrichments: Map<String, Any>,
    val geoLocation: GeoLocation?,
    val threatIntelligence: ThreatInfo?,
    val processedAt: Long
)
```

## Configuration

### Environment Variables

```bash
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export DATABASE_URL=jdbc:postgresql://localhost:5432/sentinel
export GEOIP_API_KEY=your_api_key
export THREAT_INTEL_API_KEY=your_api_key
```

### Kafka Configuration

```properties
application.id=sentinel-stream-processor
bootstrap.servers=localhost:9092
default.key.serde=org.apache.kafka.common.serialization.Serdes$StringSerde
default.value.serde=org.apache.kafka.common.serialization.Serdes$StringSerde
```

## Monitoring

### Metrics

The pipeline exposes metrics for:
- Events processed per second
- Processing latency
- Error rates
- Window lag

### Logging

Structured logging with Kotlin Logging:

```kotlin
logger.info { "Processing event: ${event.eventId}" }
logger.error(e) { "Failed to process event" }
```

## Performance

- **Throughput**: 10K+ events/second
- **Latency**: <100ms per event
- **Window Processing**: Sub-second aggregations
- **Scalability**: Horizontal scaling with Kafka partitions

## Testing

```bash
./gradlew test
```

## Deployment

### Docker

```dockerfile
FROM openjdk:17-slim
COPY build/libs/data-pipeline-1.0.0.jar /app/pipeline.jar
CMD ["java", "-jar", "/app/pipeline.jar", "stream"]
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-pipeline
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: pipeline
        image: explainai-sentinel/data-pipeline:latest
        args: ["stream"]
        env:
        - name: KAFKA_BOOTSTRAP_SERVERS
          value: "kafka:9092"
```

## Integration

### With AI Engine

```kotlin
// Send enriched events to AI engine for anomaly detection
enrichedEvents.to("ai-engine-input")
```

### With Knowledge Graph

```kotlin
// Send correlated events to knowledge graph
correlatedEvents.to("knowledge-graph-events")
```

### With Policy Engine

```kotlin
// Send high-priority events for policy evaluation
highPriorityEvents.to("policy-evaluation-queue")
```

## License

MIT License
