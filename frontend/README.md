# Fleet Telemetry & Control Frontend

Welcome to the React Frontend for the Fleet Telemetry system. This project was initialized using Vite + React + TypeScript and designed to seamlessly interface with the backend and telemetry services.

## Setup Guide

### For Person B (Backend)
1. Navigate to `/src/services/websocket.ts` and `/src/services/api.ts`.
2. Replace the mocked `startMockStream` and `ApiService` promises with your live `FastAPI` endpoint bindings.
3. The TypeScript interfaces mapped to the `TelemetryData` schemas are already rigidly defined and consumed by the UI charts. As long as your endpoints fulfill the `TelemetryData` and `Session` typed payloads, the UI (Dashboard and Replay views) will automatically hydrate correctly.

### For Person C (DevOps)
1. The `Dockerfile` and `.dockerignore` are ready at the root of the project.
2. The Docker build utilizes a multi-stage process (Node build -> Nginx alpine serving). 
3. `nginx.conf` handles frontend single-page application (SPA) routing fallbacks securely.
4. You can build and test this locally via:
   ```bash
   docker build -t fleet-telemetry-frontend .
   docker run -p 8080:80 fleet-telemetry-frontend
   ```

### For Person D (Telemetry)
1. You can review the schemas defined in `/src/services/api.ts` and `/src/services/websocket.ts` to ensure your data models match what the dashboard is programmed to digest.
2. The `Recharts` library is currently mapped to `pose.x`, `pose.y`, `pose.theta`, and `battery`.

## Running Locally

To run the frontend purely in frontend-mock-mode:
```bash
npm install
npm run dev
```
Then visit `http://localhost:5173`.
