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

Add them following to your `.env` file:
```
DB_NAME=metal_to_cloud
DB_USER=robot_admin
DB_PASSWORD=secret_password
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


## Section-Specific

### Backend
* **API Code**: The FastAPI application and core logic are located inside the `/backend` directory.

* **Database Connection**: The PostgreSQL database is fully integrated and running.

* **Data Persistence**: All database records are safely stored in the `pg_data` Docker volume, ensuring the state and telemetry data survive container restarts.

* **Local Database Inspection**: The database port is securely exposed to your local host at `127.0.0.1:5432`.

* **Active Routes**: The WebSocket traffic hubs (`/ws/frontend` and `/ws/robot/{robot_id}`) and REST endpoints (`/status`, `/telemetry/`) are live, routing traffic, and accessible at `localhost:8000`.

### Telemetry
* Integrating With Frontend:
   1. You can review the schemas defined in `frontend/src/services/api.ts` and `frontend/src/services/websocket.ts` to ensure your the robot's/agent's data models match what the dashboard is programmed to digest.
   2. The `Recharts` library is currently mapped to visualize `pose.x`, `pose.y`, `pose.theta`, and `battery`.

### DevOps
* The multi-stage `Dockerfile` (Node build -> Nginx Alpine serving) and `.dockerignore` are separated into the `/frontend` directory.

* `nginx.conf` handles frontend single-page application (SPA) routing fallbacks securely.

* The frontend is orchestrated via the root `compose.yaml` file, mapping the internal NGINX port 80 to the host port 3000.