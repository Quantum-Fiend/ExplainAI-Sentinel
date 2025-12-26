package com.explainai.sentinel.kg.core

import com.explainai.sentinel.kg.model._
import org.apache.spark.graphx._
import org.apache.spark.rdd.RDD
import org.apache.spark.SparkContext
import com.typesafe.scalalogging.LazyLogging
import scala.collection.mutable
import java.time.Instant

/**
 * Knowledge Graph Engine
 * Manages graph construction, updates, and queries
 */
class KnowledgeGraphEngine(sc: SparkContext) extends LazyLogging {
  
  private var graph: Option[Graph[GraphNode, GraphEdge]] = None
  private val nodeIndex = mutable.Map[String, Long]()
  private var nextVertexId: Long = 0L
  
  /**
   * Initialize empty graph
   */
  def initialize(): Unit = {
    val vertices: RDD[(VertexId, GraphNode)] = sc.emptyRDD
    val edges: RDD[Edge[GraphEdge]] = sc.emptyRDD
    
    graph = Some(Graph(vertices, edges))
    logger.info("Knowledge graph initialized")
  }
  
  /**
   * Add node to graph
   */
  def addNode(node: GraphNode): Unit = {
    if (!nodeIndex.contains(node.id)) {
      val vertexId = nextVertexId
      nextVertexId += 1
      
      nodeIndex(node.id) = vertexId
      
      graph = graph.map { g =>
        val newVertex = sc.parallelize(Seq((vertexId, node)))
        Graph(g.vertices.union(newVertex), g.edges)
      }
      
      logger.debug(s"Added node: ${node.id} (type: ${node.nodeType})")
    }
  }
  
  /**
   * Add edge to graph
   */
  def addEdge(edge: GraphEdge): Unit = {
    val sourceVertexId = nodeIndex.get(edge.sourceId)
    val targetVertexId = nodeIndex.get(edge.targetId)
    
    (sourceVertexId, targetVertexId) match {
      case (Some(srcId), Some(tgtId)) =>
        graph = graph.map { g =>
          val newEdge = sc.parallelize(Seq(Edge(srcId, tgtId, edge)))
          Graph(g.vertices, g.edges.union(newEdge))
        }
        logger.debug(s"Added edge: ${edge.sourceId} -> ${edge.targetId} (type: ${edge.edgeType})")
        
      case _ =>
        logger.warn(s"Cannot add edge: source or target node not found")
    }
  }
  
  /**
   * Batch add nodes and edges
   */
  def addBatch(nodes: List[GraphNode], edges: List[GraphEdge]): Unit = {
    logger.info(s"Adding batch: ${nodes.size} nodes, ${edges.size} edges")
    
    // Add all nodes first
    nodes.foreach(addNode)
    
    // Then add edges
    edges.foreach(addEdge)
  }
  
  /**
   * Find node by ID
   */
  def findNode(nodeId: String): Option[GraphNode] = {
    nodeIndex.get(nodeId).flatMap { vertexId =>
      graph.flatMap { g =>
        g.vertices.filter(_._1 == vertexId).map(_._2).collect().headOption
      }
    }
  }
  
  /**
   * Find nodes by type
   */
  def findNodesByType(nodeType: NodeType): List[GraphNode] = {
    graph.map { g =>
      g.vertices
        .filter { case (_, node) => node.nodeType == nodeType }
        .map(_._2)
        .collect()
        .toList
    }.getOrElse(List.empty)
  }
  
  /**
   * Find neighbors of a node
   */
  def findNeighbors(nodeId: String, direction: EdgeDirection = EdgeDirection.Either): List[GraphNode] = {
    nodeIndex.get(nodeId).map { vertexId =>
      graph.map { g =>
        val neighbors = direction match {
          case EdgeDirection.Out =>
            g.edges.filter(_.srcId == vertexId).map(_.dstId)
          case EdgeDirection.In =>
            g.edges.filter(_.dstId == vertexId).map(_.srcId)
          case EdgeDirection.Either =>
            g.edges
              .filter(e => e.srcId == vertexId || e.dstId == vertexId)
              .flatMap(e => Seq(e.srcId, e.dstId))
              .filter(_ != vertexId)
        }
        
        val neighborIds = neighbors.distinct().collect()
        g.vertices
          .filter { case (id, _) => neighborIds.contains(id) }
          .map(_._2)
          .collect()
          .toList
      }.getOrElse(List.empty)
    }.getOrElse(List.empty)
  }
  
  /**
   * Find shortest path between two nodes
   */
  def findShortestPath(sourceId: String, targetId: String): Option[List[GraphNode]] = {
    (nodeIndex.get(sourceId), nodeIndex.get(targetId)) match {
      case (Some(srcVertexId), Some(tgtVertexId)) =>
        graph.flatMap { g =>
          // Use Pregel for shortest path
          val initialGraph = g.mapVertices { (id, node) =>
            if (id == srcVertexId) (0.0, List(node))
            else (Double.PositiveInfinity, List.empty[GraphNode])
          }
          
          val sssp = initialGraph.pregel(
            (Double.PositiveInfinity, List.empty[GraphNode]),
            maxIterations = 10
          )(
            // Vertex program
            (id, dist, newDist) => {
              if (newDist._1 < dist._1) newDist else dist
            },
            // Send message
            triplet => {
              if (triplet.srcAttr._1 + 1 < triplet.dstAttr._1) {
                Iterator((triplet.dstId, (triplet.srcAttr._1 + 1, triplet.srcAttr._2 :+ triplet.dstAttr._2.headOption.getOrElse(triplet.dstAttr._2.head))))
              } else {
                Iterator.empty
              }
            },
            // Merge messages
            (a, b) => if (a._1 < b._1) a else b
          )
          
          val result = sssp.vertices
            .filter(_._1 == tgtVertexId)
            .map(_._2._2)
            .collect()
            .headOption
            
          result
        }
        
      case _ =>
        logger.warn(s"Cannot find path: source or target node not found")
        None
    }
  }
  
  /**
   * Calculate PageRank
   */
  def calculatePageRank(iterations: Int = 10): Map[String, Double] = {
    graph.map { g =>
      val ranks = g.pageRank(0.0001, iterations).vertices
      
      val nodeRanks = ranks.collect().map { case (vertexId, rank) =>
        nodeIndex.find(_._2 == vertexId).map { case (nodeId, _) =>
          nodeId -> rank
        }
      }.flatten.toMap
      
      logger.info(s"PageRank calculated for ${nodeRanks.size} nodes")
      nodeRanks
    }.getOrElse(Map.empty)
  }
  
  /**
   * Detect communities using label propagation
   */
  def detectCommunities(maxIterations: Int = 5): Map[String, Long] = {
    graph.map { g =>
      val communities = g.labelPropagation(maxIterations).vertices
      
      val nodeCommunities = communities.collect().map { case (vertexId, communityId) =>
        nodeIndex.find(_._2 == vertexId).map { case (nodeId, _) =>
          nodeId -> communityId
        }
      }.flatten.toMap
      
      logger.info(s"Detected ${nodeCommunities.values.toSet.size} communities")
      nodeCommunities
    }.getOrElse(Map.empty)
  }
  
  /**
   * Calculate degree centrality
   */
  def calculateDegreeCentrality(): Map[String, Int] = {
    graph.map { g =>
      val degrees = g.degrees.collect()
      
      degrees.map { case (vertexId, degree) =>
        nodeIndex.find(_._2 == vertexId).map { case (nodeId, _) =>
          nodeId -> degree
        }
      }.flatten.toMap
    }.getOrElse(Map.empty)
  }
  
  /**
   * Get graph statistics
   */
  def getStatistics(): GraphStatistics = {
    graph.map { g =>
      val numNodes = g.vertices.count()
      val numEdges = g.edges.count()
      
      val nodesByType = g.vertices
        .map { case (_, node) => (node.nodeType, 1L) }
        .reduceByKey(_ + _)
        .collect()
        .toMap
        
      val edgesByType = g.edges
        .map { case Edge(_, _, edge) => (edge.edgeType, 1L) }
        .reduceByKey(_ + _)
        .collect()
        .toMap
        
      val avgDegree = if (numNodes > 0) (2.0 * numEdges) / numNodes else 0.0
      val density = if (numNodes > 1) (2.0 * numEdges) / (numNodes * (numNodes - 1)) else 0.0
      
      val connectedComponents = g.connectedComponents().vertices
        .map(_._2)
        .distinct()
        .count()
        .toInt
      
      GraphStatistics(
        totalNodes = numNodes,
        totalEdges = numEdges,
        nodesByType = nodesByType,
        edgesByType = edgesByType,
        avgDegree = avgDegree,
        density = density,
        connectedComponents = connectedComponents,
        timestamp = Instant.now()
      )
    }.getOrElse(
      GraphStatistics(0, 0, Map.empty, Map.empty, 0.0, 0.0, 0, Instant.now())
    )
  }
  
  /**
   * Clear graph
   */
  def clear(): Unit = {
    initialize()
    nodeIndex.clear()
    nextVertexId = 0L
    logger.info("Knowledge graph cleared")
  }
}
