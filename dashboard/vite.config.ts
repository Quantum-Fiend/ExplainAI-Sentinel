import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
    server: {
        port: 3000,
        proxy: {
            '/api/runtime': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
            '/api/ai': {
                target: 'http://localhost:8001',
                changeOrigin: true,
            },
            '/api/kg': {
                target: 'http://localhost:8002',
                changeOrigin: true,
            },
            '/api/policy': {
                target: 'http://localhost:8003',
                changeOrigin: true,
            },
        },
    },
})
