# Fleet Telemetry & Control System

This repository contains the complete "Metal-to-Cloud" infrastructure for our robotic fleet telemetry system. It includes the React frontend, the FastAPI backend, the PostgreSQL database, and the ROS 2 simulated robot bridge.

## Repository Structure
The project modularized into the following folders:

- `/frontend`: Vite + React + TypeScript dashboard.

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

- Frontend Dashboard: http://localhost:3000

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
   1. You can review the schemas defined in `frontend/src/services/api.ts` and `frontend/src/services/websocket.ts` to ensure your the robot's/agent's data models match what the dashboard is programmed to digest.
   2. The `Recharts` library is currently mapped to visualize `pose.x`, `pose.y`, `pose.theta`, and `battery`.

### DevOps
* The multi-stage `Dockerfile` (Node build -> Nginx Alpine serving) and `.dockerignore` are separated into the `/frontend` directory.

* `nginx.conf` handles frontend single-page application (SPA) routing fallbacks securely.

* The robot bridge utilizes the official `osrf/ros:humble-desktop` base image to strictly isolate heavy robotics dependencies from the rest of the cloud architecture.

* All services (Frontend, Backend, Database, and Bridge) are orchestrated via the root `compose.yaml` file, networked via the internal `fleet-network`.
