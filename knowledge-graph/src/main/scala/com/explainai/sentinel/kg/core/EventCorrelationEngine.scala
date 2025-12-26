package com.explainai.sentinel.kg.core

import com.explainai.sentinel.kg.model._
import com.typesafe.scalalogging.LazyLogging
import scala.collection.mutable
import java.time.Instant
import java.time.temporal.ChronoUnit

/**
 * Event Correlation Engine
 * Correlates events based on temporal, spatial, and causal patterns
 */
class EventCorrelationEngine(
  graphEngine: KnowledgeGraphEngine,
  causalEngine: CausalReasoningEngine
) extends LazyLogging {
  
  private val correlations = mutable.ListBuffer[EventCorrelation]()
  private val eventBuffer = mutable.ListBuffer[GraphEvent]()
  
  /**
   * Add event to correlation buffer
   */
  def addEvent(event: GraphEvent): Unit = {
    eventBuffer += event
    logger.debug(s"Added event ${event.eventId} to correlation buffer")
    
    // Trigger correlation if buffer is large enough
    if (eventBuffer.size >= 10) {
      correlateEvents()
    }
  }
  
  /**
   * Correlate events in buffer
   */
  def correlateEvents(
    timeWindowSeconds: Long = 300,
    minCorrelationScore: Double = 0.5
  ): List[EventCorrelation] = {
    
    if (eventBuffer.size < 2) {
      return List.empty
    }
    
    logger.info(s"Correlating ${eventBuffer.size} events")
    
    val newCorrelations = mutable.ListBuffer[EventCorrelation]()
    val now = Instant.now()
    
    // Filter events within time window
    val recentEvents = eventBuffer.filter { event =>
      ChronoUnit.SECONDS.between(event.timestamp, now) <= timeWindowSeconds
    }
    
    // Find event clusters based on similarity
    val clusters = findEventClusters(recentEvents.toList, minCorrelationScore)
    
    // Create correlations for each cluster
    for (cluster <- clusters) {
      if (cluster.size >= 2) {
        val correlationScore = calculateClusterCorrelation(cluster)
        
        if (correlationScore >= minCorrelationScore) {
          val temporalPattern = identifyTemporalPattern(cluster)
          val causalChain = buildCausalChain(cluster)
          
          val correlation = EventCorrelation(
            correlationId = generateCorrelationId(),
            events = cluster,
            correlationScore = correlationScore,
            temporalPattern = temporalPattern,
            causalChain = causalChain,
            timestamp = Instant.now()
          )
          
          newCorrelations += correlation
          correlations += correlation
          
          logger.info(
            s"Found correlation: ${cluster.size} events, " +
            s"score: ${correlationScore}, pattern: ${temporalPattern}"
          )
        }
      }
    }
    
    // Clean up old events from buffer
    val cutoffTime = now.minusSeconds(timeWindowSeconds)
    eventBuffer.filterInPlace(_.timestamp.isAfter(cutoffTime))
    
    newCorrelations.toList
  }
  
  /**
   * Find event clusters using similarity metrics
   */
  private def findEventClusters(
    events: List[GraphEvent],
    threshold: Double
  ): List[List[GraphEvent]] = {
    
    val clusters = mutable.ListBuffer[List[GraphEvent]]()
    val visited = mutable.Set[String]()
    
    for (event <- events if !visited.contains(event.eventId)) {
      val cluster = mutable.ListBuffer[GraphEvent](event)
      visited += event.eventId
      
      // Find similar events
      for (other <- events if !visited.contains(other.eventId)) {
        val similarity = calculateEventSimilarity(event, other)
        
        if (similarity >= threshold) {
          cluster += other
          visited += other.eventId
        }
      }
      
      if (cluster.size >= 2) {
        clusters += cluster.toList
      }
    }
    
    clusters.toList
  }
  
  /**
   * Calculate similarity between two events
   */
  private def calculateEventSimilarity(event1: GraphEvent, event2: GraphEvent): Double = {
    var similarity = 0.0
    var factors = 0
    
    // Temporal proximity (30% weight)
    val timeDiff = Math.abs(ChronoUnit.SECONDS.between(event1.timestamp, event2.timestamp))
    val temporalSimilarity = Math.exp(-timeDiff / 300.0) // Decay over 5 minutes
    similarity += temporalSimilarity * 0.3
    factors += 1
    
    // Event type similarity (20% weight)
    if (event1.eventType == event2.eventType) {
      similarity += 0.2
    }
    factors += 1
    
    // Entity overlap (30% weight)
    val entityOverlap = calculateEntityOverlap(event1, event2)
    similarity += entityOverlap * 0.3
    factors += 1
    
    // Property similarity (20% weight)
    val propertySimilarity = calculatePropertySimilarity(event1.properties, event2.properties)
    similarity += propertySimilarity * 0.2
    factors += 1
    
    similarity
  }
  
  /**
   * Calculate entity overlap between events
   */
  private def calculateEntityOverlap(event1: GraphEvent, event2: GraphEvent): Double = {
    val entities1 = Set(event1.sourceNode.map(_.id), event1.targetNode.map(_.id)).flatten
    val entities2 = Set(event2.sourceNode.map(_.id), event2.targetNode.map(_.id)).flatten
    
    if (entities1.isEmpty || entities2.isEmpty) return 0.0
    
    val intersection = entities1.intersect(entities2).size.toDouble
    val union = entities1.union(entities2).size.toDouble
    
    if (union > 0) intersection / union else 0.0
  }
  
  /**
   * Calculate property similarity
   */
  private def calculatePropertySimilarity(props1: Map[String, Any], props2: Map[String, Any]): Double = {
    if (props1.isEmpty || props2.isEmpty) return 0.0
    
    val commonKeys = props1.keySet.intersect(props2.keySet)
    if (commonKeys.isEmpty) return 0.0
    
    val matchingValues = commonKeys.count { key =>
      props1(key) == props2(key)
    }
    
    matchingValues.toDouble / commonKeys.size
  }
  
  /**
   * Calculate correlation score for a cluster
   */
  private def calculateClusterCorrelation(events: List[GraphEvent]): Double = {
    if (events.size < 2) return 0.0
    
    // Calculate pairwise similarities
    val similarities = for {
      i <- events.indices
      j <- (i + 1) until events.size
    } yield calculateEventSimilarity(events(i), events(j))
    
    if (similarities.isEmpty) 0.0
    else similarities.sum / similarities.size
  }
  
  /**
   * Identify temporal pattern in event cluster
   */
  private def identifyTemporalPattern(events: List[GraphEvent]): String = {
    if (events.size < 2) return "single_event"
    
    val sortedEvents = events.sortBy(_.timestamp.toEpochMilli)
    val timeDelays = sortedEvents.sliding(2).map { pair =>
      ChronoUnit.MILLIS.between(pair.head.timestamp, pair.last.timestamp)
    }.toList
    
    if (timeDelays.isEmpty) return "simultaneous"
    
    val avgDelay = timeDelays.sum / timeDelays.size
    val variance = timeDelays.map(d => Math.pow(d - avgDelay, 2)).sum / timeDelays.size
    
    if (avgDelay < 1000) {
      "burst"  // Events within 1 second
    } else if (variance < avgDelay * 0.1) {
      "periodic"  // Regular intervals
    } else if (timeDelays.forall(_ > 0)) {
      "sequential"  // Ordered sequence
    } else {
      "irregular"
    }
  }
  
  /**
   * Build causal chain from correlated events
   */
  private def buildCausalChain(events: List[GraphEvent]): Option[List[CausalRelationship]] = {
    if (events.size < 2) return None
    
    // Infer causal relationships
    val causalRels = causalEngine.inferCausalRelationships(events, timeWindowSeconds = 300)
    
    if (causalRels.isEmpty) None
    else Some(causalRels)
  }
  
  /**
   * Generate unique correlation ID
   */
  private def generateCorrelationId(): String = {
    s"CORR-${Instant.now().toEpochMilli}-${scala.util.Random.nextInt(10000)}"
  }
  
  /**
   * Get correlations by time range
   */
  def getCorrelations(
    startTime: Option[Instant] = None,
    endTime: Option[Instant] = None
  ): List[EventCorrelation] = {
    
    correlations.filter { corr =>
      val afterStart = startTime.forall(corr.timestamp.isAfter)
      val beforeEnd = endTime.forall(corr.timestamp.isBefore)
      afterStart && beforeEnd
    }.toList
  }
  
  /**
   * Get correlations involving specific event
   */
  def getCorrelationsForEvent(eventId: String): List[EventCorrelation] = {
    correlations.filter { corr =>
      corr.events.exists(_.eventId == eventId)
    }.toList
  }
  
  /**
   * Get correlation statistics
   */
  def getStatistics(): Map[String, Any] = {
    Map(
      "total_correlations" -> correlations.size,
      "events_in_buffer" -> eventBuffer.size,
      "avg_events_per_correlation" -> {
        if (correlations.nonEmpty)
          correlations.map(_.events.size).sum.toDouble / correlations.size
        else 0.0
      },
      "temporal_patterns" -> correlations.groupBy(_.temporalPattern).mapValues(_.size)
    )
  }
  
  /**
   * Clear old correlations
   */
  def clearOldCorrelations(olderThanSeconds: Long): Unit = {
    val cutoffTime = Instant.now().minusSeconds(olderThanSeconds)
    val sizeBefore = correlations.size
    
    correlations.filterInPlace(_.timestamp.isAfter(cutoffTime))
    
    val removed = sizeBefore - correlations.size
    if (removed > 0) {
      logger.info(s"Cleared $removed old correlations")
    }
  }
}
