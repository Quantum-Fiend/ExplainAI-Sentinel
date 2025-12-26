package com.explainai.sentinel.kg.api

import akka.actor.typed.ActorSystem
import akka.actor.typed.scaladsl.Behaviors
import akka.http.scaladsl.Http
import akka.http.scaladsl.model.StatusCodes
import akka.http.scaladsl.server.Directives._
import akka.http.scaladsl.server.Route
import de.heikoseeberger.akkahttpcirce.FailFastCirceSupport._
import io.circe.generic.auto._
import io.circe.syntax._
import com.explainai.sentinel.kg.core._
import com.explainai.sentinel.kg.model._
import com.typesafe.config.ConfigFactory
import com.typesafe.scalalogging.LazyLogging
import org.apache.spark.{SparkConf, SparkContext}

import scala.concurrent.{ExecutionContextExecutor, Future}
import scala.util.{Failure, Success}
import java.time.Instant

/**
 * Knowledge Graph API Server
 * Provides REST API for graph operations, causal reasoning, and event correlation
 */
object KnowledgeGraphServer extends LazyLogging {
  
  // Request/Response models
  case class AddNodeRequest(node: GraphNode)
  case class AddEdgeRequest(edge: GraphEdge)
  case class BatchUpdateRequest(nodes: List[GraphNode], edges: List[GraphEdge])
  case class QueryRequest(nodeType: Option[String], properties: Map[String, Any])
  case class PathRequest(sourceId: String, targetId: String)
  case class CausalQueryRequest(
    intervention: Map[String, Any],
    outcome: String,
    confounders: List[String] = List.empty
  )
  case class EventRequest(event: GraphEvent)
  
  case class ApiResponse(
    success: Boolean,
    message: String,
    data: Option[Any] = None
  )
  
  def main(args: Array[String]): Unit = {
    // Load configuration
    val config = ConfigFactory.load()
    val kgConfig = config.getConfig("knowledge_graph")
    
    // Initialize Spark
    val sparkConf = new SparkConf()
      .setAppName("ExplainAI-KnowledgeGraph")
      .setMaster("local[*]")
    val sc = new SparkContext(sparkConf)
    
    // Initialize engines
    val graphEngine = new KnowledgeGraphEngine(sc)
    graphEngine.initialize()
    
    val causalEngine = new CausalReasoningEngine(graphEngine)
    val correlationEngine = new EventCorrelationEngine(graphEngine, causalEngine)
    
    // Create Akka HTTP server
    implicit val system: ActorSystem[Nothing] = ActorSystem(Behaviors.empty, "kg-api-system")
    implicit val executionContext: ExecutionContextExecutor = system.executionContext
    
    val routes = createRoutes(graphEngine, causalEngine, correlationEngine)
    
    val host = kgConfig.getString("api.host")
    val port = kgConfig.getInt("api.port")
    
    val bindingFuture = Http().newServerAt(host, port).bind(routes)
    
    bindingFuture.onComplete {
      case Success(binding) =>
        val address = binding.localAddress
        logger.info(s"Knowledge Graph API server online at http://${address.getHostString}:${address.getPort}/")
        
      case Failure(ex) =>
        logger.error(s"Failed to bind HTTP server: ${ex.getMessage}")
        system.terminate()
    }
  }
  
  def createRoutes(
    graphEngine: KnowledgeGraphEngine,
    causalEngine: CausalReasoningEngine,
    correlationEngine: EventCorrelationEngine
  ): Route = {
    
    pathPrefix("api" / "v1") {
      concat(
        // Health check
        path("health") {
          get {
            complete(StatusCodes.OK, ApiResponse(
              success = true,
              message = "Knowledge Graph Engine is healthy"
            ))
          }
        },
        
        // Graph operations
        pathPrefix("graph") {
          concat(
            // Add node
            path("nodes") {
              post {
                entity(as[AddNodeRequest]) { request =>
                  graphEngine.addNode(request.node)
                  complete(StatusCodes.Created, ApiResponse(
                    success = true,
                    message = s"Node ${request.node.id} added successfully"
                  ))
                }
              }
            },
            
            // Get node
            path("nodes" / Segment) { nodeId =>
              get {
                graphEngine.findNode(nodeId) match {
                  case Some(node) =>
                    complete(StatusCodes.OK, ApiResponse(
                      success = true,
                      message = "Node found",
                      data = Some(node.asJson)
                    ))
                  case None =>
                    complete(StatusCodes.NotFound, ApiResponse(
                      success = false,
                      message = s"Node $nodeId not found"
                    ))
                }
              }
            },
            
            // Add edge
            path("edges") {
              post {
                entity(as[AddEdgeRequest]) { request =>
                  graphEngine.addEdge(request.edge)
                  complete(StatusCodes.Created, ApiResponse(
                    success = true,
                    message = "Edge added successfully"
                  ))
                }
              }
            },
            
            // Batch update
            path("batch") {
              post {
                entity(as[BatchUpdateRequest]) { request =>
                  graphEngine.addBatch(request.nodes, request.edges)
                  complete(StatusCodes.OK, ApiResponse(
                    success = true,
                    message = s"Added ${request.nodes.size} nodes and ${request.edges.size} edges"
                  ))
                }
              }
            },
            
            // Find neighbors
            path("nodes" / Segment / "neighbors") { nodeId =>
              get {
                val neighbors = graphEngine.findNeighbors(nodeId)
                complete(StatusCodes.OK, ApiResponse(
                  success = true,
                  message = s"Found ${neighbors.size} neighbors",
                  data = Some(neighbors.asJson)
                ))
              }
            },
            
            // Shortest path
            path("path") {
              post {
                entity(as[PathRequest]) { request =>
                  graphEngine.findShortestPath(request.sourceId, request.targetId) match {
                    case Some(path) =>
                      complete(StatusCodes.OK, ApiResponse(
                        success = true,
                        message = s"Path found with ${path.size} nodes",
                        data = Some(path.asJson)
                      ))
                    case None =>
                      complete(StatusCodes.NotFound, ApiResponse(
                        success = false,
                        message = "No path found"
                      ))
                  }
                }
              }
            },
            
            // Graph statistics
            path("statistics") {
              get {
                val stats = graphEngine.getStatistics()
                complete(StatusCodes.OK, ApiResponse(
                  success = true,
                  message = "Statistics retrieved",
                  data = Some(stats.asJson)
                ))
              }
            }
          )
        },
        
        // Analytics
        pathPrefix("analytics") {
          concat(
            // PageRank
            path("pagerank") {
              get {
                parameters("iterations".as[Int] ? 10) { iterations =>
                  val ranks = graphEngine.calculatePageRank(iterations)
                  complete(StatusCodes.OK, ApiResponse(
                    success = true,
                    message = s"PageRank calculated for ${ranks.size} nodes",
                    data = Some(ranks.asJson)
                  ))
                }
              }
            },
            
            // Community detection
            path("communities") {
              get {
                val communities = graphEngine.detectCommunities()
                complete(StatusCodes.OK, ApiResponse(
                  success = true,
                  message = s"Detected ${communities.values.toSet.size} communities",
                  data = Some(communities.asJson)
                ))
              }
            },
            
            // Centrality
            path("centrality") {
              get {
                val centrality = graphEngine.calculateDegreeCentrality()
                complete(StatusCodes.OK, ApiResponse(
                  success = true,
                  message = "Centrality calculated",
                  data = Some(centrality.asJson)
                ))
              }
            }
          )
        },
        
        // Causal reasoning
        pathPrefix("causal") {
          concat(
            // Causal inference
            path("infer") {
              post {
                entity(as[CausalQueryRequest]) { request =>
                  val query = CausalQuery(
                    intervention = request.intervention,
                    outcome = request.outcome,
                    confounders = request.confounders
                  )
                  
                  val result = causalEngine.performCausalInference(query)
                  complete(StatusCodes.OK, ApiResponse(
                    success = true,
                    message = "Causal inference completed",
                    data = Some(result.asJson)
                  ))
                }
              }
            },
            
            // Find causes
            path("causes" / Segment) { effectId =>
              get {
                parameters("maxDepth".as[Int] ? 3) { maxDepth =>
                  val causes = causalEngine.findCauses(effectId, maxDepth)
                  complete(StatusCodes.OK, ApiResponse(
                    success = true,
                    message = s"Found ${causes.size} causal relationships",
                    data = Some(causes.asJson)
                  ))
                }
              }
            },
            
            // Find effects
            path("effects" / Segment) { causeId =>
              get {
                parameters("maxDepth".as[Int] ? 3) { maxDepth =>
                  val effects = causalEngine.findEffects(causeId, maxDepth)
                  complete(StatusCodes.OK, ApiResponse(
                    success = true,
                    message = s"Found ${effects.size} causal relationships",
                    data = Some(effects.asJson)
                  ))
                }
              }
            }
          )
        },
        
        // Event correlation
        pathPrefix("events") {
          concat(
            // Add event
            path("add") {
              post {
                entity(as[EventRequest]) { request =>
                  correlationEngine.addEvent(request.event)
                  complete(StatusCodes.Accepted, ApiResponse(
                    success = true,
                    message = "Event added to correlation buffer"
                  ))
                }
              }
            },
            
            // Trigger correlation
            path("correlate") {
              post {
                val correlations = correlationEngine.correlateEvents()
                complete(StatusCodes.OK, ApiResponse(
                  success = true,
                  message = s"Found ${correlations.size} correlations",
                  data = Some(correlations.asJson)
                ))
              }
            },
            
            // Get correlations
            path("correlations") {
              get {
                val correlations = correlationEngine.getCorrelations()
                complete(StatusCodes.OK, ApiResponse(
                  success = true,
                  message = s"Retrieved ${correlations.size} correlations",
                  data = Some(correlations.asJson)
                ))
              }
            },
            
            // Correlation statistics
            path("statistics") {
              get {
                val stats = correlationEngine.getStatistics()
                complete(StatusCodes.OK, ApiResponse(
                  success = true,
                  message = "Statistics retrieved",
                  data = Some(stats.asJson)
                ))
              }
            }
          )
        }
      )
    }
  }
}
