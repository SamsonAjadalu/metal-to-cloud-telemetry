# Fleet Telemetry & Control System

This repository contains the complete "Metal-to-Cloud" infrastructure for our robotic fleet telemetry system. It includes the React frontend, the FastAPI backend, the PostgreSQL database, and (soon!) the ROS 2 simulated robot bridge.

## Repository Structure
The project modularized into the following folders:

- `/frontend`: Vite + React + TypeScript dashboard.

- `/backend`: FastAPI application and WebSocket server.

- `compose.yaml`: The master orchestration file that runs the cloud infrastructure.

- Soon: `/telemetry_sim`: ROS 2 Python bridge for Gazebo TurtleBot3 simulation. (Note: Runs outside of Docker).


## How to Run the Infrastructure (for Local Development)

1. **Set up Environment Variables**

Before running the cluster, create a `.env` file in the root of the repository (next to `compose.yaml`).
(Note: `.env` should be gitignored and not be committed).

When the following are agreed upon between us add them your `.env` file as follows:
```
DB_NAME=telemetry_db
DB_USER=telemetry_user
DB_PASSWORD=securepassword
DB_PORT=5432
```

2. **Start the Cluster**

From the root directory, run:

```bash
docker compose up --build
```

3. **Access the Services**

Once Docker finishes booting up and the database healthcheck passes, the following services will be available:

- Frontend Dashboard: http://localhost:3000

- Backend API: http://localhost:8000

- Backend API Docs: http://localhost:8000/docs

- PostgreSQL Database: `localhost:5432`

To shut down the infrastructure, press `Ctrl + C` in the terminal, or run `docker compose down`.


## Section-Specific Guides

### For Backend
* API code is inside `/backend`.

* The `requirements.txt` is seeded with `fastapi[standard]` and `websockets` to get the server running.

* **Database Access**: A Postgres container is running and mapped to your environment variables. You will need to add your preferred DB driver (e.g.,`psycopg2-binary`, `sqlalchemy`) to `requirements.txt` to connect. You can use the injected `DATABASE_URL` environment variable.

* **Required Routes**: You can expose the following WebSocket routes for the system to connect end-to-end:
   - `ws://localhost:8000/ws/frontend` (For the React UI)
   - `ws://localhost:8000/ws/robot/{robot_id}` (For the robots)

* **Integrating With Frontend**:
   1. Navigate to `frontend/src/services/websocket.ts` and `frontend/src/services/api.ts`.
   2. Replace the mocked `startMockStream` and `ApiService` promises with your live FastAPI endpoint bindings once the backend is containerized.
   3. The TypeScript interfaces mapped to the `TelemetryData` schemas are rigidly defined and consumed by the UI charts. As long as your endpoints fulfill the `TelemetryData` and `Session` typed payloads, the UI (Dashboard and Replay views) will automatically hydrate correctly.

### For Telemetry
* **Integrating With Frontend**:
   1. You can review the schemas defined in `frontend/src/services/api.ts` and `frontend/src/services/websocket.ts` to ensure your the robot's/agent's data models match what the dashboard is programmed to digest.
   2. The `Recharts` library is currently mapped to visualize `pose.x`, `pose.y`, `pose.theta`, and `battery`.

### For DevOps
* The multi-stage `Dockerfile` (Node build -> Nginx Alpine serving) and `.dockerignore` are separated into the `/frontend` directory.

* `nginx.conf` handles frontend single-page application (SPA) routing fallbacks securely.

* The frontend is orchestrated via the root `compose.yaml` file, mapping the internal NGINX port 80 to the host port 3000.
