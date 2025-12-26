# Knowledge Graph & Causal Reasoning Engine

Production-ready knowledge graph and causal reasoning system built with Scala and Spark GraphX.

## Features

- **Distributed Graph Processing**: Spark GraphX for large-scale graph analytics
- **Causal Inference**: Do-calculus based causal reasoning with temporal correlation
- **Event Correlation**: Automatic event clustering and pattern detection
- **Graph Analytics**: PageRank, community detection, centrality metrics
- **REST API**: Akka HTTP-based API for all operations
- **Real-time Processing**: Streaming event correlation and analysis

## Architecture

```
knowledge-graph/
├── src/main/scala/com/explainai/sentinel/kg/
│   ├── model/
│   │   └── Models.scala              # Domain models
│   ├── core/
│   │   ├── KnowledgeGraphEngine.scala    # Graph engine
│   │   ├── CausalReasoningEngine.scala   # Causal inference
│   │   └── EventCorrelationEngine.scala  # Event correlation
│   └── api/
│       └── KnowledgeGraphServer.scala    # HTTP API server
├── src/main/resources/
│   └── application.conf              # Configuration
└── build.sbt                         # Build configuration
```

## Installation

### Prerequisites

- Java 11 or higher
- Scala 2.13
- SBT 1.9+
- Apache Spark 3.5

### Build

```bash
sbt compile
sbt assembly  # Create fat JAR
```

## Running

### Start the Server

```bash
sbt run
```

Or using the fat JAR:

```bash
java -jar target/scala-2.13/knowledge-graph-engine-assembly-1.0.0.jar
```

The API will be available at `http://localhost:8002`

## API Documentation

### Graph Operations

#### Add Node

```bash
curl -X POST http://localhost:8002/api/v1/graph/nodes \
  -H "Content-Type: application/json" \
  -d '{
    "node": {
      "id": "service-1",
      "nodeType": "Service",
      "properties": {"name": "auth-service", "version": "1.0"},
      "timestamp": "2024-01-01T00:00:00Z",
      "version": 1,
      "metadata": {}
    }
  }'
```

#### Add Edge

```bash
curl -X POST http://localhost:8002/api/v1/graph/edges \
  -H "Content-Type: application/json" \
  -d '{
    "edge": {
      "id": "edge-1",
      "sourceId": "service-1",
      "targetId": "service-2",
      "edgeType": "Communicates",
      "weight": 1.0,
      "timestamp": "2024-01-01T00:00:00Z",
      "confidence": 0.95
    }
  }'
```

#### Find Shortest Path

```bash
curl -X POST http://localhost:8002/api/v1/graph/path \
  -H "Content-Type: application/json" \
  -d '{
    "sourceId": "service-1",
    "targetId": "service-5"
  }'
```

#### Get Graph Statistics

```bash
curl http://localhost:8002/api/v1/graph/statistics
```

### Analytics

#### Calculate PageRank

```bash
curl "http://localhost:8002/api/v1/analytics/pagerank?iterations=10"
```

#### Detect Communities

```bash
curl http://localhost:8002/api/v1/analytics/communities
```

#### Calculate Centrality

```bash
curl http://localhost:8002/api/v1/analytics/centrality
```

### Causal Reasoning

#### Perform Causal Inference

```bash
curl -X POST http://localhost:8002/api/v1/causal/infer \
  -H "Content-Type: application/json" \
  -d '{
    "intervention": {"service-1": "restart"},
    "outcome": "service-5",
    "confounders": []
  }'
```

#### Find Causes

```bash
curl "http://localhost:8002/api/v1/causal/causes/event-123?maxDepth=3"
```

#### Find Effects

```bash
curl "http://localhost:8002/api/v1/causal/effects/event-456?maxDepth=3"
```

### Event Correlation

#### Add Event

```bash
curl -X POST http://localhost:8002/api/v1/events/add \
  -H "Content-Type: application/json" \
  -d '{
    "event": {
      "eventId": "evt-001",
      "eventType": "failed_auth",
      "timestamp": "2024-01-01T00:00:00Z",
      "properties": {"user": "admin", "attempts": 5}
    }
  }'
```

#### Trigger Correlation

```bash
curl -X POST http://localhost:8002/api/v1/events/correlate
```

#### Get Correlations

```bash
curl http://localhost:8002/api/v1/events/correlations
```

## Configuration

Edit `src/main/resources/application.conf`:

```hocon
knowledge_graph {
  storage {
    type = "neo4j"  # or "in-memory", "distributed"
    neo4j {
      uri = "bolt://localhost:7687"
      username = "neo4j"
      password = "password"
    }
  }
  
  analytics {
    algorithms {
      pagerank {
        iterations = 10
        damping_factor = 0.85
      }
    }
  }
  
  causal_reasoning {
    inference {
      confidence_threshold = 0.7
      max_causal_depth = 5
    }
  }
  
  api {
    host = "0.0.0.0"
    port = 8002
  }
}
```

## Usage Examples

### Scala

```scala
import com.explainai.sentinel.kg.core._
import com.explainai.sentinel.kg.model._
import org.apache.spark.{SparkConf, SparkContext}

// Initialize Spark
val conf = new SparkConf().setAppName("KG-Example").setMaster("local[*]")
val sc = new SparkContext(conf)

// Create engines
val graphEngine = new KnowledgeGraphEngine(sc)
graphEngine.initialize()

val causalEngine = new CausalReasoningEngine(graphEngine)
val correlationEngine = new EventCorrelationEngine(graphEngine, causalEngine)

// Add nodes
val node1 = GraphNode("service-1", NodeType.Service, Map("name" -> "auth"))
val node2 = GraphNode("service-2", NodeType.Service, Map("name" -> "api"))

graphEngine.addNode(node1)
graphEngine.addNode(node2)

// Add edge
val edge = GraphEdge("e1", "service-1", "service-2", EdgeType.Communicates)
graphEngine.addEdge(edge)

// Find path
val path = graphEngine.findShortestPath("service-1", "service-2")

// Calculate PageRank
val ranks = graphEngine.calculatePageRank(10)

// Causal inference
val query = CausalQuery(
  intervention = Map("service-1" -> "restart"),
  outcome = "service-2"
)
val result = causalEngine.performCausalInference(query)
```

## Performance

- **Graph Operations**: O(1) for node/edge addition, O(V+E) for traversal
- **PageRank**: O(iterations × E) distributed across Spark cluster
- **Causal Inference**: O(path_length × relationships)
- **Event Correlation**: O(n²) for clustering, optimized with time windows

## License

MIT License
