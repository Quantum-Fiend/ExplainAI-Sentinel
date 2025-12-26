export interface AnomalyDetection {
    is_anomaly: boolean;
    confidence: number;
    anomaly_score: number;
    threat_detection?: ThreatDetection;
    explanation?: Explanation;
    timestamp: string;
    request_id: string;
}

export interface ThreatDetection {
    threat_id: string;
    category: string;
    level: 'critical' | 'high' | 'medium' | 'low' | 'info';
    confidence: number;
    description: string;
    recommended_actions: string[];
}

export interface Explanation {
    summary: string;
    top_contributing_features: Record<string, number>;
    model_agreement: number;
    confidence_breakdown: Record<string, number>;
}

export interface GraphNode {
    id: string;
    nodeType: string;
    properties: Record<string, any>;
    timestamp: string;
}

export interface GraphEdge {
    id: string;
    sourceId: string;
    targetId: string;
    edgeType: string;
    weight: number;
    confidence: number;
}

export interface CausalRelationship {
    cause: GraphNode;
    effect: GraphNode;
    causalStrength: number;
    confidence: number;
    evidence: string[];
    temporalDelay?: number;
    mechanism?: string;
}

export interface EventCorrelation {
    correlationId: string;
    events: any[];
    correlationScore: number;
    temporalPattern: string;
    causalChain?: CausalRelationship[];
    timestamp: string;
}

export interface Policy {
    id: string;
    name: string;
    description: string;
    priority: 'Critical' | 'High' | 'Medium' | 'Low';
    enabled: boolean;
    conditions: any;
    actions: any[];
    metadata: Record<string, string>;
    created_at: string;
    updated_at: string;
    version: number;
}

export interface TrustScore {
    entity_id: string;
    score: number;
    factors: Record<string, number>;
    last_updated: string;
    expires_at?: string;
}

export interface Violation {
    id: string;
    policy_id: string;
    context: any;
    action_taken: any;
    timestamp: string;
    severity: string;
}

export interface ServiceInfo {
    id: string;
    name: string;
    status: 'healthy' | 'degraded' | 'unhealthy';
    endpoint: string;
    lastHeartbeat: string;
    metadata: Record<string, string>;
}

export interface SystemMetrics {
    cpu_usage: number;
    memory_usage: number;
    network_in: number;
    network_out: number;
    active_connections: number;
    requests_per_second: number;
    error_rate: number;
    timestamp: string;
}

export interface Alert {
    id: string;
    severity: 'critical' | 'high' | 'medium' | 'low';
    title: string;
    message: string;
    source: string;
    timestamp: string;
    acknowledged: boolean;
    resolved: boolean;
}
