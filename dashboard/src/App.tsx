import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Threats from './pages/Threats';
import KnowledgeGraph from './pages/KnowledgeGraph';
import Policies from './pages/Policies';
import TrustScores from './pages/TrustScores';
import Services from './pages/Services';
import './index.css';

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            refetchOnWindowFocus: false,
            retry: 1,
            staleTime: 30000,
        },
    },
});

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>
                <Layout>
                    <Routes>
                        <Route path="/" element={<Navigate to="/dashboard" replace />} />
                        <Route path="/dashboard" element={<Dashboard />} />
                        <Route path="/threats" element={<Threats />} />
                        <Route path="/knowledge-graph" element={<KnowledgeGraph />} />
                        <Route path="/policies" element={<Policies />} />
                        <Route path="/trust-scores" element={<TrustScores />} />
                        <Route path="/services" element={<Services />} />
                    </Routes>
                </Layout>
            </BrowserRouter>
            <Toaster position="top-right" richColors />
        </QueryClientProvider>
    );
}

export default App;
