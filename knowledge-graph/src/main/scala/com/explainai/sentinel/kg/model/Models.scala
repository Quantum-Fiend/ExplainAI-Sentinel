package com.explainai.sentinel.kg.model

import java.time.Instant

/**
 * Core domain models for knowledge graph
 */

// Node types in the knowledge graph
sealed trait NodeType
object NodeType {
  case object Service extends NodeType
  case object Device extends NodeType
  case object User extends NodeType
  case object Event extends NodeType
  case object Threat extends NodeType
  case object Policy extends NodeType
  case object Resource extends NodeType
  case object Alert extends NodeType
}

// Edge types representing relationships
sealed trait EdgeType
object EdgeType {
  case object Causes extends EdgeType
  case object CorrelatesWith extends EdgeType
  case object Triggers extends EdgeType
  case object DependsOn extends EdgeType
  case object Communicates extends EdgeType
  case object Accesses extends EdgeType
  case object Owns extends EdgeType
  case object Monitors extends EdgeType
  case object Mitigates extends EdgeType
}

// Graph Node
case class GraphNode(
  id: String,
  nodeType: NodeType,
  properties: Map[String, Any],
  timestamp: Instant = Instant.now(),
  version: Int = 1,
  metadata: Map[String, String] = Map.empty
)

// Graph Edge
case class GraphEdge(
  id: String,
  sourceId: String,
  targetId: String,
  edgeType: EdgeType,
  weight: Double = 1.0,
  properties: Map[String, Any] = Map.empty,
  timestamp: Instant = Instant.now(),
  confidence: Double = 1.0
)

// Event for graph updates
case class GraphEvent(
  eventId: String,
  eventType: String,
  sourceNode: Option[GraphNode],
  targetNode: Option[GraphNode],
  edge: Option[GraphEdge],
  timestamp: Instant,
  properties: Map[String, Any] = Map.empty
)

// Causal relationship
case class CausalRelationship(
  cause: GraphNode,
  effect: GraphNode,
  causalStrength: Double,
  confidence: Double,
  evidence: List[String],
  temporalDelay: Option[Long] = None, // milliseconds
  mechanism: Option[String] = None
)

// Event correlation
case class EventCorrelation(
  correlationId: String,
  events: List[GraphEvent],
  correlationScore: Double,
  temporalPattern: String,
  causalChain: Option[List[CausalRelationship]] = None,
  timestamp: Instant
)

// Graph query result
case class GraphQueryResult(
  nodes: List[GraphNode],
  edges: List[GraphEdge],
  metadata: Map[String, Any] = Map.empty,
  executionTimeMs: Long
)

// Causal query
case class CausalQuery(
  intervention: Map[String, Any],
  outcome: String,
  confounders: List[String] = List.empty,
  timeRange: Option[(Instant, Instant)] = None
)

// Causal inference result
case class CausalInferenceResult(
  query: CausalQuery,
  estimatedEffect: Double,
  confidence: Double,
  causalPath: List[GraphNode],
  counterfactuals: List[Map[String, Any]] = List.empty,
  explanation: String
)

// Graph statistics
case class GraphStatistics(
  totalNodes: Long,
  totalEdges: Long,
  nodesByType: Map[NodeType, Long],
  edgesByType: Map[EdgeType, Long],
  avgDegree: Double,
  density: Double,
  connectedComponents: Int,
  timestamp: Instant
)

// Pattern matching result
case class PatternMatch(
  matchId: String,
  pattern: String,
  matchedNodes: List[GraphNode],
  matchedEdges: List[GraphEdge],
  confidence: Double,
  timestamp: Instant
)
