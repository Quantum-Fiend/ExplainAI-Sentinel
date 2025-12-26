# ExplainAI-Sentinel Dashboard

Modern, real-time security dashboard built with React, TypeScript, and Tailwind CSS.

## Features

- **Real-time Monitoring**: Live metrics and threat detection
- **Interactive Visualizations**: Charts, graphs, and network diagrams
- **Knowledge Graph Explorer**: Visual exploration of causal relationships
- **Policy Management**: Create, edit, and manage security policies
- **Trust Score Dashboard**: Monitor entity trust scores
- **Alert Management**: Real-time alerts with severity levels
- **Service Health**: Monitor all platform services

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Vite** - Build tool
- **React Query** - Data fetching and caching
- **Recharts** - Charts and visualizations
- **D3.js** - Advanced visualizations
- **Vis.js** - Network graphs
- **Zustand** - State management
- **Axios** - HTTP client

## Installation

```bash
npm install
```

## Development

```bash
npm run dev
```

The dashboard will be available at `http://localhost:3000`

## Build

```bash
npm run build
```

## Project Structure

```
dashboard/
├── src/
│   ├── api/
│   │   └── client.ts          # API client
│   ├── components/
│   │   └── Layout.tsx         # Main layout
│   ├── pages/
│   │   ├── Dashboard.tsx      # Main dashboard
│   │   ├── Threats.tsx        # Threat detection
│   │   ├── KnowledgeGraph.tsx # Graph visualization
│   │   ├── Policies.tsx       # Policy management
│   │   ├── TrustScores.tsx    # Trust scoring
│   │   └── Services.tsx       # Service monitoring
│   ├── types/
│   │   └── index.ts           # TypeScript types
│   ├── lib/
│   │   └── utils.ts           # Utility functions
│   ├── App.tsx                # Main app component
│   ├── main.tsx               # Entry point
│   └── index.css              # Global styles
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.js
```

## API Integration

The dashboard connects to all backend services:

- **AI Engine** (port 8001): `/api/ai/*`
- **Knowledge Graph** (port 8002): `/api/kg/*`
- **Policy Engine** (port 8003): `/api/policy/*`
- **Runtime** (port 8000): `/api/runtime/*`

API proxies are configured in `vite.config.ts`.

## Pages

### Dashboard
- Real-time system metrics
- Active threat count
- Anomaly detection statistics
- Recent alerts feed
- Resource usage charts

### Threats
- Detected threats list
- Threat details with explanations
- Confidence scores
- Recommended actions
- Threat timeline

### Knowledge Graph
- Interactive graph visualization
- Node and edge exploration
- Causal relationship viewer
- Event correlation display
- PageRank and community detection

### Policies
- Policy list and management
- Create/edit/delete policies
- Enable/disable policies
- Policy evaluation testing
- Violation history

### Trust Scores
- Entity trust scores
- Trust factor breakdown
- Score history
- Trust threshold management
- Entity search and filtering

### Services
- Service health status
- Service registry
- Heartbeat monitoring
- Service metrics
- Task scheduler status

## Customization

### Colors

Edit `tailwind.config.js` to customize the color palette:

```javascript
theme: {
  extend: {
    colors: {
      primary: { ... },
      danger: { ... },
      success: { ... },
      warning: { ... },
    },
  },
}
```

### API Endpoints

Update `src/api/client.ts` to modify API endpoints or add new services.

## Environment Variables

Create `.env` file:

```
VITE_API_BASE_URL=http://localhost
VITE_AI_PORT=8001
VITE_KG_PORT=8002
VITE_POLICY_PORT=8003
VITE_RUNTIME_PORT=8000
```

## Development Mode

The dashboard includes mock data for development when backend services are unavailable. See `src/api/client.ts` for mock data generators.

## Production Deployment

1. Build the application:
```bash
npm run build
```

2. Serve the `dist` folder with any static file server:
```bash
npm run preview
```

Or deploy to:
- Vercel
- Netlify
- AWS S3 + CloudFront
- Nginx
- Apache

## Performance

- **Code Splitting**: Automatic route-based code splitting
- **Lazy Loading**: Components loaded on demand
- **Caching**: React Query caches API responses
- **Optimized Builds**: Vite produces optimized production bundles

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

MIT License
