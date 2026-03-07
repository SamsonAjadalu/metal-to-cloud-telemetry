# Fleet Telemetry & Control Frontend (Updated)

Welcome to the React Frontend for the Fleet Telemetry system. This project was initialized using Vite + React + TypeScript and designed to seamlessly interface with the backend and telemetry services.

## Setup Guide

### For Backend
1. Navigate to `frontend/src/services/websocket.ts` and `frontend/src/services/api.ts`.
2. Replace the mocked `startMockStream` and `ApiService` promises with your live FastAPI endpoint bindings once the backend is containerized.
3. The TypeScript interfaces mapped to the `TelemetryData` schemas are rigidly defined and consumed by the UI charts. As long as your endpoints fulfill the `TelemetryData` and `Session` typed payloads, the UI (Dashboard and Replay views) will automatically hydrate correctly.

### For Telemetry
1. You can review the schemas defined in `frontend/src/services/api.ts` and `frontend/src/services/websocket.ts` to ensure your the robot's/agent's data models match what the dashboard is programmed to digest.
2. The `Recharts` library is currently mapped to visualize `pose.x`, `pose.y`, `pose.theta`, and `battery`.

### For DevOps
1. The multi-stage `Dockerfile` (Node build -> Nginx Alpine serving) and `.dockerignore` are separated into the `/frontend` directory.

2. `nginx.conf` handles frontend single-page application (SPA) routing fallbacks securely.

3. The frontend is orchestrated via the root `compose.yaml` file, mapping the internal NGINX port 80 to the host port 3000.

## Running Locally

### Method 1: Full Stack via Docker
To run the frontend using the production-ready NGINX container alongside the rest of the infrastructure, run this from the root directory:
```bash
docker compose up --build
```
Then visit `http://localhost:3000`.

### Method 2: Frontend-Only Reload Mode:
To run the frontend purely in isolated mock-mode for rapid UI development, run these commands from inside the `/frontend` directory:

```bash
npm install
npm run dev
```
Then visit `http://localhost:5173`.
