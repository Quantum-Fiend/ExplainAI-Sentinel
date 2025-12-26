name := "knowledge-graph-engine"

version := "1.0.0"

scalaVersion := "2.13.12"

libraryDependencies ++= Seq(
  // Graph Processing
  "org.apache.spark" %% "spark-core" % "3.5.0",
  "org.apache.spark" %% "spark-sql" % "3.5.0",
  "org.apache.spark" %% "spark-graphx" % "3.5.0",
  
  // Graph Databases
  "com.michaelpollmeier" %% "gremlin-scala" % "3.7.1.0",
  "org.neo4j.driver" % "neo4j-java-driver" % "5.14.0",
  
  // Causal Inference
  "org.apache.commons" % "commons-math3" % "3.6.1",
  
  // JSON Processing
  "io.circe" %% "circe-core" % "0.14.6",
  "io.circe" %% "circe-generic" % "0.14.6",
  "io.circe" %% "circe-parser" % "0.14.6",
  
  // HTTP Server
  "com.typesafe.akka" %% "akka-http" % "10.5.3",
  "com.typesafe.akka" %% "akka-stream" % "2.8.5",
  "com.typesafe.akka" %% "akka-actor-typed" % "2.8.5",
  "de.heikoseeberger" %% "akka-http-circe" % "1.39.2",
  
  // Configuration
  "com.typesafe" % "config" % "1.4.3",
  
  // Logging
  "com.typesafe.scala-logging" %% "scala-logging" % "3.9.5",
  "ch.qos.logback" % "logback-classic" % "1.4.11",
  
  // Testing
  "org.scalatest" %% "scalatest" % "3.2.17" % Test,
  "org.scalatestplus" %% "mockito-4-11" % "3.2.17.0" % Test
)

// Compiler options
scalacOptions ++= Seq(
  "-encoding", "UTF-8",
  "-feature",
  "-deprecation",
  "-unchecked",
  "-language:implicitConversions",
  "-language:higherKinds",
  "-Xlint"
)

// Assembly settings for fat JAR
assembly / assemblyMergeStrategy := {
  case PathList("META-INF", xs @ _*) => MergeStrategy.discard
  case "reference.conf" => MergeStrategy.concat
  case x => MergeStrategy.first
}

assembly / mainClass := Some("com.explainai.sentinel.kg.KnowledgeGraphServer")
