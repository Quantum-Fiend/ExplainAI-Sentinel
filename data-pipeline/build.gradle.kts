plugins {
    kotlin("jvm") version "1.9.21"
    kotlin("plugin.serialization") version "1.9.21"
    application
}

group = "com.explainai.sentinel"
version = "1.0.0"

repositories {
    mavenCentral()
    maven { url = uri("https://packages.confluent.io/maven/") }
}

dependencies {
    // Kotlin
    implementation(kotlin("stdlib"))
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.2")
    
    // Kafka & Streaming
    implementation("org.apache.kafka:kafka-streams:3.6.1")
    implementation("org.apache.kafka:kafka-clients:3.6.1")
    implementation("io.confluent:kafka-streams-avro-serde:7.5.3")
    
    // Data Processing
    implementation("org.apache.arrow:arrow-vector:14.0.1")
    implementation("org.apache.arrow:arrow-memory-netty:14.0.1")
    implementation("com.github.doyaaaaaken:kotlin-csv-jvm:1.9.2")
    
    // Validation
    implementation("com.github.kittinunf.result:result:5.5.0")
    implementation("io.konform:konform-jvm:0.4.0")
    
    // Database
    implementation("org.jetbrains.exposed:exposed-core:0.45.0")
    implementation("org.jetbrains.exposed:exposed-dao:0.45.0")
    implementation("org.jetbrains.exposed:exposed-jdbc:0.45.0")
    implementation("org.postgresql:postgresql:42.7.1")
    
    // HTTP Client
    implementation("io.ktor:ktor-client-core:2.3.7")
    implementation("io.ktor:ktor-client-cio:2.3.7")
    implementation("io.ktor:ktor-client-content-negotiation:2.3.7")
    implementation("io.ktor:ktor-serialization-kotlinx-json:2.3.7")
    
    // Logging
    implementation("io.github.microutils:kotlin-logging-jvm:3.0.5")
    implementation("ch.qos.logback:logback-classic:1.4.14")
    
    // Testing
    testImplementation(kotlin("test"))
    testImplementation("io.mockk:mockk:1.13.8")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")
}

tasks.test {
    useJUnitPlatform()
}

kotlin {
    jvmToolchain(24)
}

application {
    mainClass.set("com.explainai.sentinel.pipeline.MainKt")
}
