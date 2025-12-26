"""
FastAPI-based AI Model Serving
Provides REST API for AI/ML inference with monitoring and metrics
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np
import uvicorn
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from loguru import logger
import yaml
import sys

# Import our modules
sys.path.append('.')
from anomaly_detector import EnsembleAnomalyDetector, AnomalyResult
from explainer import ExplainableAI, Explanation
from threat_intelligence import ThreatIntelligence, ThreatDetection


# Pydantic models for API
class DetectionRequest(BaseModel):
    features: Dict[str, float] = Field(..., description="Feature dictionary")
    explain: bool = Field(default=True, description="Include explanation")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class DetectionResponse(BaseModel):
    is_anomaly: bool
    confidence: float
    anomaly_score: float
    threat_detection: Optional[Dict] = None
    explanation: Optional[Dict] = None
    timestamp: str
    request_id: str


class HealthResponse(BaseModel):
    status: str
    version: str
    models_loaded: bool
    uptime_seconds: float


class MetricsResponse(BaseModel):
    total_requests: int
    total_anomalies: int
    avg_latency_ms: float
    model_accuracy: float


# Prometheus metrics
REQUEST_COUNT = Counter('ai_requests_total', 'Total AI inference requests')
ANOMALY_COUNT = Counter('anomalies_detected_total', 'Total anomalies detected')
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency in seconds')
EXPLANATION_LATENCY = Histogram('explanation_latency_seconds', 'Explanation generation latency')


class AIModelServer:
    """AI Model Serving Server"""
    
    def __init__(self, config_path: str = "config/ai_config.yaml"):
        self.app = FastAPI(
            title="ExplainAI-Sentinel AI Engine",
            description="AI-driven security and anomaly detection API",
            version="1.0.0"
        )
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)['ai_engine']
            
        # Initialize models
        self.anomaly_detector = None
        self.explainer = None
        self.threat_intel = None
        self.start_time = datetime.now()
        
        # Setup middleware
        self._setup_middleware()
        
        # Setup routes
        self._setup_routes()
        
        logger.info("AI Model Server initialized")
        
    def _setup_middleware(self):
        """Setup CORS and other middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.on_event("startup")
        async def startup_event():
            """Initialize models on startup"""
            await self.load_models()
            
        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint"""
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            return HealthResponse(
                status="healthy",
                version="1.0.0",
                models_loaded=self.anomaly_detector is not None,
                uptime_seconds=uptime
            )
            
        @self.app.post("/detect", response_model=DetectionResponse)
        @REQUEST_LATENCY.time()
        async def detect_anomaly(request: DetectionRequest):
            """
            Detect anomalies and threats
            
            Args:
                request: Detection request with features
                
            Returns:
                Detection response with results and explanations
            """
            REQUEST_COUNT.inc()
            
            if self.anomaly_detector is None:
                raise HTTPException(status_code=503, detail="Models not loaded")
                
            try:
                # Convert features to array
                feature_array = np.array(list(request.features.values()))
                
                # Detect anomaly
                anomaly_result = self.anomaly_detector.detect(feature_array)
                
                if anomaly_result.is_anomaly:
                    ANOMALY_COUNT.inc()
                    
                # Detect threats
                threat_detection = None
                if self.threat_intel and anomaly_result.is_anomaly:
                    threat = self.threat_intel.detect_threat(
                        request.features,
                        request.context
                    )
                    if threat:
                        threat_detection = {
                            'threat_id': threat.threat_id,
                            'category': threat.category.value,
                            'level': threat.level.value,
                            'confidence': threat.confidence,
                            'description': threat.description,
                            'recommended_actions': threat.recommended_actions
                        }
                        
                # Generate explanation
                explanation = None
                if request.explain and self.explainer:
                    with EXPLANATION_LATENCY.time():
                        explanation = anomaly_result.explanation
                        
                # Generate request ID
                request_id = f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                
                response = DetectionResponse(
                    is_anomaly=anomaly_result.is_anomaly,
                    confidence=anomaly_result.confidence,
                    anomaly_score=anomaly_result.anomaly_score,
                    threat_detection=threat_detection,
                    explanation=explanation if request.explain else None,
                    timestamp=datetime.now().isoformat(),
                    request_id=request_id
                )
                
                return response
                
            except Exception as e:
                logger.error(f"Detection failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/metrics")
        async def get_metrics():
            """Prometheus metrics endpoint"""
            return Response(
                content=generate_latest(),
                media_type=CONTENT_TYPE_LATEST
            )
            
        @self.app.get("/stats", response_model=MetricsResponse)
        async def get_statistics():
            """Get model statistics"""
            
            # Get threat statistics
            threat_stats = {}
            if self.threat_intel:
                threat_stats = self.threat_intel.get_threat_statistics()
                
            return MetricsResponse(
                total_requests=int(REQUEST_COUNT._value.get()),
                total_anomalies=int(ANOMALY_COUNT._value.get()),
                avg_latency_ms=REQUEST_LATENCY._sum.get() / max(REQUEST_LATENCY._count.get(), 1) * 1000,
                model_accuracy=0.92  # Placeholder - calculate from validation set
            )
            
        @self.app.post("/train")
        async def trigger_training(background_tasks: BackgroundTasks):
            """Trigger model retraining"""
            background_tasks.add_task(self.retrain_models)
            return {"message": "Training triggered", "status": "processing"}
            
    async def load_models(self):
        """Load AI models"""
        try:
            logger.info("Loading AI models...")
            
            # Initialize anomaly detector
            anomaly_config = self.config['models']['anomaly_detection']
            self.anomaly_detector = EnsembleAnomalyDetector(anomaly_config)
            
            # Generate synthetic training data (in production, load real data)
            np.random.seed(42)
            X_train = np.random.randn(1000, 15)
            feature_names = [
                'cpu_usage', 'memory_usage', 'network_connections',
                'failed_auth', 'process_count', 'outbound_bytes',
                'inbound_bytes', 'unique_ips', 'port_scans',
                'file_modifications', 'registry_changes', 'external_conn',
                'privilege_changes', 'lateral_moves', 'data_access'
            ]
            
            self.anomaly_detector.train(X_train, feature_names)
            
            # Initialize explainer
            if self.config['explainability']['enabled']:
                explainer_config = self.config['explainability']
                self.explainer = ExplainableAI(explainer_config)
                
            # Initialize threat intelligence
            threat_config = {}
            self.threat_intel = ThreatIntelligence(threat_config)
            
            # Train threat classifier
            y_train = np.random.randint(0, 4, 1000)
            self.threat_intel.train_classifier(X_train, y_train, feature_names)
            
            logger.info("All models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise
            
    async def retrain_models(self):
        """Retrain models with new data"""
        logger.info("Starting model retraining...")
        
        try:
            # In production, load new training data
            # For now, use synthetic data
            np.random.seed(int(datetime.now().timestamp()))
            X_train = np.random.randn(1000, 15)
            y_train = np.random.randint(0, 4, 1000)
            
            # Retrain anomaly detector
            if self.anomaly_detector:
                self.anomaly_detector.train(X_train)
                
            # Retrain threat classifier
            if self.threat_intel:
                feature_names = self.anomaly_detector.feature_names
                self.threat_intel.train_classifier(X_train, y_train, feature_names)
                
            logger.info("Model retraining completed")
            
        except Exception as e:
            logger.error(f"Retraining failed: {e}")
            
    def run(self, host: str = "0.0.0.0", port: int = 8001):
        """Run the server"""
        api_config = self.config.get('api', {})
        
        uvicorn.run(
            self.app,
            host=api_config.get('host', host),
            port=api_config.get('port', port),
            workers=api_config.get('workers', 4),
            log_level="info"
        )


if __name__ == "__main__":
    server = AIModelServer()
    server.run()
