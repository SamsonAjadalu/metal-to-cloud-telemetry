# Fleet Telemetry & Control System

This repository contains the complete "Metal-to-Cloud" infrastructure
for our robotic fleet telemetry system. It includes the React frontend,
the FastAPI backend, the PostgreSQL database, and the ROS 2 simulated
robot bridge.

## Repository Structure

The project is modularized into the following folders:
- `/frontend`: Vite + React + TypeScript dashboard.
- `/backend`: FastAPI application and WebSocket server.
- `/robot_bridge`: ROS 2 Python bridge that translates robot telemetry and commands.
- `compose.yaml`: The master orchestration file that defines the infrastructure footprint.

## Production Deployment (Docker Swarm & CI/CD)

### High Availability Architecture

The production `compose.yaml` enforces the following scaling and
placement rules to guarantee zero downtime:

-   **Frontend:** `replicas: 2` (Load-balanced across the Swarm).
-   **API:** `replicas: 1` (Single WebSocket traffic hub to ensure
    real-time state consistency).
-   **Database:** `replicas: 1` (Pinned to a specific storage node via
    the `role=database` label to protect the persistent volume).

### CI/CD Pipeline

Pushes or merged Pull Requests to the `prod` branch automatically
trigger the deployment pipeline. The pipeline:

1.  Builds the latest frontend and backend Docker images.
2.  Pushes the images to Docker Hub.
3.  SSHes into the Swarm Manager as `deploy_user`.
4.  Executes a rolling, zero-downtime update via
    `docker service update`, with automated rollback protection if a
    container fails to start.

### Security & Secrets Management

Production database credentials and environment variables are **not
managed via the repository**.

They are stored securely on the Droplet in a dedicated, restricted file and injected at deployment runtime.