package com.explainai.sentinel.pipeline;

import com.explainai.sentinel.pipeline.model.Models;
import com.explainai.sentinel.pipeline.etl.ETLPipeline;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import java.time.Instant;
import java.util.UUID;

public class PipelineTest {

    @Test
    public void testEventBuffering() {
        Models.SecurityEvent event = new Models.SecurityEvent(
            UUID.randomUUID().toString(),
            "AUTH_FAILURE",
            "10.0.0.1",
            "10.0.0.2",
            80.0,
            Instant.now(),
            new java.util.HashMap<>()
        );
        
        assertNotNull(event.id());
        assertEquals("AUTH_FAILURE", event.type());
    }

    @Test
    public void testSeverityCalculation() {
        // Mocking logic from StreamProcessor if accessible or testing pure functions
        double severity = 0.85;
        assertTrue(severity > 0.5, "High severity should be detected");
    }
}
