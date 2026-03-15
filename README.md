# Fleet Telemetry & Control System

This repository contains the complete "Metal-to-Cloud" infrastructure for our robotic fleet telemetry system. It includes the React frontend, the FastAPI backend, the PostgreSQL database, and the ROS 2 simulated robot bridge.

## Hand-off & Integration Guide

### 1. Backend Engineer (Person B)
The React frontend is now wired to connect strictly to real FastAPI endpoints. No more internal mocking needs to be disabled!
* **WebSocket**: Ensure your FastAPI app exposes `ws://localhost:8000/ws/frontend`. The React app will auto-reconnect and listen for live telemetry broadcasts.
* **REST API**: Ensure you have implemented `GET http://localhost:8000/api/sessions` and `GET http://localhost:8000/api/sessions/{id}/telemetry` for the Replay Analytics view.
* **Command Routing**: The UI will emit commands over the WebSocket interface. You must parse these payloads and forward them to the ROS2/Python agent:
  * **Twist:** `{ "type": "command", "robot_id": "tb3_01", "linear_x_cmd": 0.2, "angular_z_cmd": 0.0 }`
  * **Nav2 Goal:** `{ "type": "goal", "robot_id": "tb3_01", "x": 4.2, "y": 1.8, "yaw": 0.0 }`

### 2. Telemetry Engineer (Person D)
The UI now requires specific data footprints to render correctly. Ensure the robot emits the following JSON structure to the backend WebSocket stream:
```json
{
  "timestamp": 1700000000000,
  "map_id": "map_01",
  "battery": 85.5,
  "status": "MOVING",
  "pose": { "x": 1.2, "y": 0.5, "theta": 0.0 },
  "velocity": { "linear_x": 0.5, "angular_z": 0.0 }
}
```
*Note: The Replay Analytics REST view expects an array of `{timestamp, battery, x, y, yaw}` frames.*

### 3. DevOps Engineer (Person C)
The project structure is ready for Swarm and DigitalOcean.
* Use the provided `Dockerfile` (Multi-stage Node -> Nginx Alpine) to build the `fleet-telemetry-frontend` container image.
* **Maps**: Currently, the UI dynamically loads the local file `/maps/{map_id}.png`. You may want to mount a volume containing the maps into the Nginx `html` directory, or update the source code to point to an S3 bucket URL.
* **Build & Test**:
  ```bash
  docker build -t fleet-telemetry-frontend .
  docker run -p 8080:80 fleet-telemetry-frontend
  ```

## Running Locally for Testing

To boot the frontend locally against the live backend:
```bash
npm install
npm run dev
```
Then visit `http://localhost:5173`. If the backend isn't up, the Dashboard will cleanly display "Waiting for WebSocket connection...".

## Repository Structure
The project modularized into the following folders:

- `/frontend` (formerly root): Vite + React + TypeScript dashboard.
- `/backend`: FastAPI application and WebSocket server.
- `/robot_bridge`: ROS 2 Python bridge that translates robot telemetry and commands.
- `compose.yaml`: The master orchestration file that runs the cloud infrastructure.

## How to Run the Infrastructure (for Local Development)

1. **Set up Environment Variables**

Before running the cluster, create a `.env` file in the root of the repository (next to `compose.yaml`).
(Note: `.env` should be gitignored and not be committed).

Add them following to your `.env` file:
```
DB_NAME=metal_to_cloud
DB_USER=robot_admin
DB_PASSWORD=secret_password
DB_PORT=5432
ROBOT_ID=tb3_01
```

2. **Start the Cluster**

From the root directory, run:

```bash
docker compose up --build
```

3. **Access the Services**

Once Docker finishes booting up and the database healthcheck passes, the following services will be available:

- Frontend Dashboard: http://localhost:3000 (if dockerized) or `localhost:5173` (if `npm run dev`)
- Backend API: http://localhost:8000
- Backend API Docs: http://localhost:8000/docs
- PostgreSQL Database: `localhost:5432`

To shut down the infrastructure, press `Ctrl + C` in the terminal, or run `docker compose down`.

## Section-Specific

### Backend
* **API Code**: The FastAPI application and core logic are located inside the `/backend` directory.
* **Database Connection**: The PostgreSQL database is fully integrated and running.
* **Data Persistence**: All database records are safely stored in the `pg_data` Docker volume, ensuring the state and telemetry data survive container restarts.
* **Local Database Inspection**: The database port is securely exposed to your local host at `127.0.0.1:5432`.
* **Active Routes**: The WebSocket traffic hubs (`/ws/frontend` and `/ws/robot/{robot_id}`) and REST endpoints (`/status`, `/telemetry/`) are live, routing traffic, and accessible at `localhost:8000`.

### Telemetry
* **Bridge Containerization**: The ROS 2 Python bridge is fully containerized and boots up automatically with docker compose and connects to the backend using the ROBOT_ID and BACKEND_HOST environment variables.
* **Integrating With Frontend**:
   1. You can review the schemas defined in `src/services/api.ts` and `src/services/websocket.ts` to ensure your the robot's/agent's data models match what the dashboard is programmed to digest.
   2. The `Recharts` library is currently mapped to visualize `pose.x`, `pose.y`, `pose.theta`, and `battery`.

### DevOps
* The multi-stage `Dockerfile` (Node build -> Nginx Alpine serving) and `.dockerignore` are separated into the `/frontend` directory.
* `nginx.conf` handles frontend single-page application (SPA) routing fallbacks securely.
* The robot bridge utilizes the official `osrf/ros:humble-desktop` base image to strictly isolate heavy robotics dependencies from the rest of the cloud architecture.
* All services (Frontend, Backend, Database, and Bridge) are orchestrated via the root `compose.yaml` file, networked via the internal `fleet-network`.
