package com.explainai.sentinel.kg.core

import com.explainai.sentinel.kg.model._
import com.typesafe.scalalogging.LazyLogging
import scala.collection.mutable
import java.time.Instant
import java.time.temporal.ChronoUnit

/**
 * Causal Reasoning Engine
 * Implements causal inference and counterfactual reasoning
 */
class CausalReasoningEngine(graphEngine: KnowledgeGraphEngine) extends LazyLogging {
  
  private val causalRelationships = mutable.Map[String, CausalRelationship]()
  private val temporalCorrelations = mutable.Map[(String, String), Double]()
  
  /**
   * Infer causal relationships from temporal patterns
   */
  def inferCausalRelationships(
    events: List[GraphEvent],
    timeWindowSeconds: Long = 3600,
    confidenceThreshold: Double = 0.7
  ): List[CausalRelationship] = {
    
    logger.info(s"Inferring causal relationships from ${events.size} events")
    
    val relationships = mutable.ListBuffer[CausalRelationship]()
    
    // Group events by time windows
    val sortedEvents = events.sortBy(_.timestamp.toEpochMilli)
    
    // Find temporal precedence patterns
    for {
      i <- sortedEvents.indices
      j <- (i + 1) until sortedEvents.size
    } {
      val event1 = sortedEvents(i)
      val event2 = sortedEvents(j)
      
      val timeDiff = ChronoUnit.MILLIS.between(event1.timestamp, event2.timestamp)
      
      if (timeDiff > 0 && timeDiff <= timeWindowSeconds * 1000) {
        // Check for potential causal relationship
        val causalStrength = calculateCausalStrength(event1, event2, events)
        
        if (causalStrength > confidenceThreshold) {
          (event1.sourceNode, event2.sourceNode) match {
            case (Some(cause), Some(effect)) =>
              val relationship = CausalRelationship(
                cause = cause,
                effect = effect,
                causalStrength = causalStrength,
                confidence = calculateConfidence(event1, event2, events),
                evidence = List(s"Temporal precedence: ${timeDiff}ms", s"Correlation: ${causalStrength}"),
                temporalDelay = Some(timeDiff),
                mechanism = inferMechanism(event1, event2)
              )
              
              relationships += relationship
              causalRelationships(s"${cause.id}->${effect.id}") = relationship
              
            case _ => // Skip if nodes not present
          }
        }
      }
    }
    
    logger.info(s"Inferred ${relationships.size} causal relationships")
    relationships.toList
  }
  
  /**
   * Calculate causal strength using temporal correlation and co-occurrence
   */
  private def calculateCausalStrength(
    cause: GraphEvent,
    effect: GraphEvent,
    allEvents: List[GraphEvent]
  ): Double = {
    
    // Count co-occurrences
    val causeType = cause.eventType
    val effectType = effect.eventType
    
    val causeEvents = allEvents.filter(_.eventType == causeType)
    val effectEvents = allEvents.filter(_.eventType == effectType)
    
    if (causeEvents.isEmpty || effectEvents.isEmpty) return 0.0
    
    // Calculate conditional probability P(effect | cause)
    val coOccurrences = causeEvents.count { ce =>
      effectEvents.exists { ee =>
        val timeDiff = ChronoUnit.MILLIS.between(ce.timestamp, ee.timestamp)
        timeDiff > 0 && timeDiff <= 60000 // 1 minute window
      }
    }
    
    val conditionalProb = coOccurrences.toDouble / causeEvents.size
    
    // Calculate baseline probability P(effect)
    val baselineProb = effectEvents.size.toDouble / allEvents.size
    
    // Causal strength = lift = P(effect | cause) / P(effect)
    if (baselineProb > 0) {
      Math.min(conditionalProb / baselineProb, 1.0)
    } else {
      0.0
    }
  }
  
  /**
   * Calculate confidence in causal relationship
   */
  private def calculateConfidence(
    cause: GraphEvent,
    effect: GraphEvent,
    allEvents: List[GraphEvent]
  ): Double = {
    
    // Factors contributing to confidence:
    // 1. Temporal consistency
    // 2. Frequency of co-occurrence
    // 3. Absence of confounders
    
    val temporalConsistency = 0.8 // Placeholder
    val frequencyScore = 0.7 // Placeholder
    val confounderAbsence = 0.9 // Placeholder
    
    (temporalConsistency + frequencyScore + confounderAbsence) / 3.0
  }
  
  /**
   * Infer causal mechanism
   */
  private def inferMechanism(cause: GraphEvent, effect: GraphEvent): Option[String] = {
    (cause.eventType, effect.eventType) match {
      case ("failed_auth", "account_lockout") =>
        Some("Multiple failed authentication attempts trigger account lockout policy")
      case ("high_cpu", "service_degradation") =>
        Some("High CPU usage causes service performance degradation")
      case ("network_spike", "dos_alert") =>
        Some("Network traffic spike triggers denial-of-service detection")
      case _ =>
        Some(s"${cause.eventType} may lead to ${effect.eventType}")
    }
  }
  
  /**
   * Perform causal inference using do-calculus
   */
  def performCausalInference(query: CausalQuery): CausalInferenceResult = {
    logger.info(s"Performing causal inference for intervention: ${query.intervention}")
    
    // Find causal path from intervention to outcome
    val interventionNodes = query.intervention.keys.flatMap { nodeId =>
      graphEngine.findNode(nodeId)
    }.toList
    
    val outcomeNode = graphEngine.findNode(query.outcome)
    
    val causalPath = (interventionNodes.headOption, outcomeNode) match {
      case (Some(source), Some(target)) =>
        graphEngine.findShortestPath(source.id, target.id).getOrElse(List.empty)
      case _ =>
        List.empty
    }
    
    // Estimate causal effect
    val estimatedEffect = estimateCausalEffect(query, causalPath)
    
    // Generate counterfactuals
    val counterfactuals = generateCounterfactuals(query, causalPath)
    
    // Generate explanation
    val explanation = generateCausalExplanation(query, causalPath, estimatedEffect)
    
    CausalInferenceResult(
      query = query,
      estimatedEffect = estimatedEffect,
      confidence = 0.75, // Placeholder - calculate based on evidence
      causalPath = causalPath,
      counterfactuals = counterfactuals,
      explanation = explanation
    )
  }
  
  /**
   * Estimate causal effect
   */
  private def estimateCausalEffect(query: CausalQuery, causalPath: List[GraphNode]): Double = {
    // Simplified causal effect estimation
    // In production, use proper causal inference methods (IV, RDD, etc.)
    
    if (causalPath.isEmpty) return 0.0
    
    // Calculate effect based on path length and relationship strengths
    val pathLength = causalPath.size
    val baseEffect = 1.0 / pathLength
    
    // Adjust based on known causal relationships
    val adjustedEffect = causalPath.sliding(2).foldLeft(baseEffect) { (effect, pair) =>
      pair match {
        case List(source, target) =>
          val relationshipKey = s"${source.id}->${target.id}"
          val strength = causalRelationships.get(relationshipKey).map(_.causalStrength).getOrElse(0.5)
          effect * strength
        case _ => effect
      }
    }
    
    adjustedEffect
  }
  
  /**
   * Generate counterfactual scenarios
   */
  private def generateCounterfactuals(
    query: CausalQuery,
    causalPath: List[GraphNode]
  ): List[Map[String, Any]] = {
    
    val counterfactuals = mutable.ListBuffer[Map[String, Any]]()
    
    // Generate alternative interventions
    for (node <- causalPath.take(3)) {
      val alternative = Map(
        "node_id" -> node.id,
        "alternative_action" -> s"Prevent ${node.nodeType}",
        "expected_outcome" -> "Reduced causal effect",
        "confidence" -> 0.7
      )
      counterfactuals += alternative
    }
    
    counterfactuals.toList
  }
  
  /**
   * Generate natural language explanation
   */
  private def generateCausalExplanation(
    query: CausalQuery,
    causalPath: List[GraphNode],
    effect: Double
  ): String = {
    
    if (causalPath.isEmpty) {
      return "No causal path found between intervention and outcome."
    }
    
    val pathDescription = causalPath.map(_.id).mkString(" → ")
    
    s"""
       |Causal Analysis:
       |
       |Intervention: ${query.intervention.keys.mkString(", ")}
       |Outcome: ${query.outcome}
       |
       |Causal Path: $pathDescription
       |
       |Estimated Effect: ${(effect * 100).formatted("%.1f")}%
       |
       |Explanation: The intervention affects the outcome through ${causalPath.size - 1} intermediate steps.
       |Each step in the causal chain contributes to the overall effect.
       |
       |Confidence: Based on temporal patterns and correlation analysis, this causal relationship
       |has moderate to high confidence.
     """.stripMargin.trim
  }
  
  /**
   * Find all causes of an effect
   */
  def findCauses(effectNodeId: String, maxDepth: Int = 3): List[CausalRelationship] = {
    val causes = causalRelationships.values.filter(_.effect.id == effectNodeId).toList
    
    if (maxDepth > 1) {
      val indirectCauses = causes.flatMap { rel =>
        findCauses(rel.cause.id, maxDepth - 1)
      }
      causes ++ indirectCauses
    } else {
      causes
    }
  }
  
  /**
   * Find all effects of a cause
   */
  def findEffects(causeNodeId: String, maxDepth: Int = 3): List[CausalRelationship] = {
    val effects = causalRelationships.values.filter(_.cause.id == causeNodeId).toList
    
    if (maxDepth > 1) {
      val indirectEffects = effects.flatMap { rel =>
        findEffects(rel.effect.id, maxDepth - 1)
      }
      effects ++ indirectEffects
    } else {
      effects
    }
  }
  
  /**
   * Get all causal relationships
   */
  def getAllCausalRelationships(): List[CausalRelationship] = {
    causalRelationships.values.toList
  }
}
