import axios from 'axios';
import type {
    AnomalyDetection,
    GraphNode,
    GraphEdge,
    EventCorrelation,
    Policy,
    TrustScore,
    Violation,
    ServiceInfo,
    SystemMetrics,
    Alert,
} from '@/types';

const api = axios.create({
    baseURL: '/api',
    timeout: 30000,
});

// AI Engine API
export const aiApi = {
    detect: async (features: Record<string, number>) => {
        const { data } = await api.post<AnomalyDetection>('/ai/detect', {
            features,
            explain: true,
        });
        return data;
    },

    getStats: async () => {
        const { data } = await api.get('/ai/stats');
        return data;
    },

    getMetrics: async () => {
        const { data } = await api.get('/ai/metrics');
        return data;
    },
};

// Knowledge Graph API
export const kgApi = {
    addNode: async (node: GraphNode) => {
        const { data } = await api.post('/kg/v1/graph/nodes', { node });
        return data;
    },

    getNode: async (id: string) => {
        const { data } = await api.get<GraphNode>(`/kg/v1/graph/nodes/${id}`);
        return data;
    },

    addEdge: async (edge: GraphEdge) => {
        const { data } = await api.post('/kg/v1/graph/edges', { edge });
        return data;
    },

    getStatistics: async () => {
        const { data } = await api.get('/kg/v1/graph/statistics');
        return data;
    },

    getPageRank: async (iterations: number = 10) => {
        const { data } = await api.get(`/kg/v1/analytics/pagerank?iterations=${iterations}`);
        return data;
    },

    getCommunities: async () => {
        const { data } = await api.get('/kg/v1/analytics/communities');
        return data;
    },

    getCorrelations: async () => {
        const { data } = await api.get<EventCorrelation[]>('/kg/v1/events/correlations');
        return data;
    },

    performCausalInference: async (intervention: any, outcome: string) => {
        const { data } = await api.post('/kg/v1/causal/infer', {
            intervention,
            outcome,
        });
        return data;
    },
};

// Policy Engine API
export const policyApi = {
    listPolicies: async (enabled?: boolean) => {
        const params = enabled !== undefined ? { enabled } : {};
        const { data } = await api.get<Policy[]>('/policy/policies', { params });
        return data;
    },

    getPolicy: async (id: string) => {
        const { data } = await api.get<Policy>(`/policy/policies/${id}`);
        return data;
    },

    createPolicy: async (policy: Partial<Policy>) => {
        const { data } = await api.post('/policy/policies', policy);
        return data;
    },

    updatePolicy: async (id: string, policy: Partial<Policy>) => {
        const { data } = await api.put(`/policy/policies/${id}`, policy);
        return data;
    },

    deletePolicy: async (id: string) => {
        const { data } = await api.delete(`/policy/policies/${id}`);
        return data;
    },

    enablePolicy: async (id: string) => {
        const { data } = await api.put(`/policy/policies/${id}/enable`);
        return data;
    },

    disablePolicy: async (id: string) => {
        const { data } = await api.put(`/policy/policies/${id}/disable`);
        return data;
    },

    getTrustScore: async (entityId: string) => {
        const { data } = await api.get<TrustScore>(`/policy/trust/${entityId}`);
        return data;
    },

    updateTrustScore: async (entityId: string, factors: Record<string, number>) => {
        const { data } = await api.put(`/policy/trust/${entityId}`, { factors });
        return data;
    },

    getViolations: async (limit: number = 50) => {
        const { data } = await api.get<Violation[]>('/policy/violations', {
            params: { limit },
        });
        return data;
    },

    getStatistics: async () => {
        const { data } = await api.get('/policy/statistics');
        return data;
    },
};

// Runtime API
export const runtimeApi = {
    getServices: async () => {
        const { data } = await api.get<ServiceInfo[]>('/runtime/services');
        return data;
    },

    getHealth: async () => {
        const { data } = await api.get('/runtime/health');
        return data;
    },

    getMetrics: async () => {
        const { data } = await api.get<SystemMetrics>('/runtime/metrics');
        return data;
    },
};

// Mock data for development
export const mockData = {
    alerts: (): Alert[] => [
        {
            id: '1',
            severity: 'critical',
            title: 'Intrusion Attempt Detected',
            message: 'Multiple failed authentication attempts from suspicious IP',
            source: 'AI Engine',
            timestamp: new Date().toISOString(),
            acknowledged: false,
            resolved: false,
        },
        {
            id: '2',
            severity: 'high',
            title: 'High CPU Usage',
            message: 'Service auth-service exceeding 85% CPU usage',
            source: 'Runtime',
            timestamp: new Date(Date.now() - 300000).toISOString(),
            acknowledged: true,
            resolved: false,
        },
        {
            id: '3',
            severity: 'medium',
            title: 'Trust Score Degraded',
            message: 'User user-123 trust score dropped below threshold',
            source: 'Policy Engine',
            timestamp: new Date(Date.now() - 600000).toISOString(),
            acknowledged: true,
            resolved: true,
        },
    ],

    metrics: (): SystemMetrics => ({
        cpu_usage: 45 + Math.random() * 20,
        memory_usage: 60 + Math.random() * 15,
        network_in: 1000 + Math.random() * 500,
        network_out: 800 + Math.random() * 400,
        active_connections: Math.floor(100 + Math.random() * 50),
        requests_per_second: Math.floor(500 + Math.random() * 200),
        error_rate: Math.random() * 2,
        timestamp: new Date().toISOString(),
    }),
};

export default api;
