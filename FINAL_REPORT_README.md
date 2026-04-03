# Metal-to-Cloud Telemetry: Fleet Orchestration & Monitoring

## Video Demo

**URL:** [YouTube]

This video (1–5 minutes) walks through the live dashboard, user flow, Docker/PostgreSQL/Swarm highlights, monitoring or health checks, and the **deployed** application URL in the browser.

---

## 1. Team Information

| Name | Student # | Email | Role |
| :--- | :--- | :--- | :--- |
| Hassan Mahdi | [Insert #] | [Insert Email] | Frontend Engineering |
| Yulong Sheng | [Insert #] | [Insert Email] | Backend & API Engineering |
| Yamoah Attafuah | [Insert #] | [Insert Email] | Cloud DevOps & Orchestration |
| Samson Ajadalu | [Insert #] | [Insert Email] | Telemetry & Robotics Integration |

---

## 2. Motivation

As robotics deploy in increasingly complex environments, the ability to monitor, debug, and control these systems remotely has become a critical bottleneck. Traditional robotics stacks often lack a simple, cloud-native path for real-time telemetry and persistent mission history. When a robot fails in the field, operators need to know exactly what happened leading up to the failure.

Our team chose this project to bridge the gap between edge robotics and cloud infrastructure. We built a "metal-to-cloud" pipeline that allows operators to view live telemetry from autonomous agents (both simulated and physical) and persist that data for historical playback. This system is designed for test engineers and robotics developers who require a low-latency, high-reliability connection to their fleet.

---

## 3. Objectives

Our primary goal was to create a robust, bidirectional data pipeline utilizing modern cloud orchestration. The specific objectives achieved include:

1. **Real-Time Streaming:** Implementing a low-latency WebSocket connection to stream live telemetry (pose, battery, status) from a ROS 2 agent to a cloud backend.
2. **Data Persistence:** Designing a reliable database architecture to store mission sessions and time-series telemetry data for post-mission analysis.
3. **Operator Dashboard:** Developing a responsive web interface for live monitoring, historical session replay, and basic fleet command/control.
4. **Cloud-Native Orchestration:** Deploying the entire software stack using Docker Swarm to ensure high availability, easy scaling, and automated recovery.

---

## 4. Technical Stack

Our architecture is split into three main layers, entirely containerized and orchestrated via Docker Swarm.

- **Frontend (UI):** React + TypeScript (built with Vite). Chosen for its component-based architecture, allowing us to build a modular, high-performance dashboard that handles rapid state changes from WebSocket streams.
- **Backend (API):** Python + FastAPI. Chosen for its native asynchronous support, which is essential for managing simultaneous REST requests and high-frequency WebSocket connections from multiple robots.
- **Database:** PostgreSQL 15. Chosen for its reliability and strong support for relational time-series data. Accessed via SQLAlchemy ORM.
- **Robotics Integration:** ROS 2 (Humble) + Gazebo. The industry standard for robotics simulation and message passing.
- **Orchestration & Cloud:** Docker Swarm on DigitalOcean Droplets.
  - *Why Swarm over Kubernetes?* For our specific timeline and fleet size, Docker Swarm provided the necessary high availability and replica management without the massive operational overhead of managing a full Kubernetes control plane. It allowed us to maintain configuration parity between local development (`docker compose`) and production deployment.

---

## 5. Features & Implementation

Our application fulfills the course requirements through the following features:

| Feature | Description | Course Requirement Fulfilled |
| :--- | :--- | :--- |
| **Live Telemetry Dashboard** | A real-time web interface displaying robot pose, battery life, and active status via WebSockets. | WebSockets (Advanced) & UI Development |
| **Mission Replay** | Operators can query past sessions from the database and "replay" the robot's telemetry history. | PostgreSQL & Data Persistence |
| **Containerized Deployment** | The Frontend, Backend, and Database are all isolated in individual Docker containers. | Docker Containerization |
| **High-Availability Swarm** | The application is deployed across a DigitalOcean Docker Swarm, ensuring the API and UI remain available even if a node fails. | Orchestration (Swarm/K8s) |
| **Persistent Storage Volumes** | PostgreSQL utilizes named Docker volumes mounted to DigitalOcean Block Storage to ensure telemetry data survives container restarts. | Storage |

Our codebase comprises approximately **[Insert Total LOC]** lines of code as measured with `cloc`, excluding `node_modules/`, build artifacts, and non-source files per course guidance. Primary languages: **TypeScript/JavaScript** (frontend), **Python** (backend and ROS bridge), **YAML** (Compose and CI).

---

## 6. User Guide

**Live Application URL:** [DigitalOcean live URL here]

### Monitoring a Live Session

1. Navigate to the live URL. The default view is the **Fleet Dashboard**.
2. If a robot is actively publishing data via the ROS 2 bridge, it will appear in the "Active Agents" list.
3. Click on a specific agent to view its real-time telemetry stream (Pose X/Y/Theta, Battery percentage).

### Replaying a Past Mission

1. Click the **Sessions** tab in the navigation bar.
2. Select a completed mission from the historical list.
3. The dashboard will retrieve the telemetry logs from the PostgreSQL database and populate the view with the historical path and data.

---

## 7. Development Guide

### Environment Setup

1. Clone the repository: `git clone https://github.com/SamsonAjadalu/metal-to-cloud-telemetry.git`
2. Install Docker and Docker Compose on the development machine.
3. Copy environment templates for the ROS bridge (repo root):

   ```bash
   cp .env.telemetry.example .env.telemetry
   ```

   For the API, set **`DATABASE_URL`** (and any DB variables required by `compose.yaml`) in a **`.env`** file or the shell environment, consistent with `backend/database.py` and the `db` service in `compose.yaml`.

### Local Execution (Full Stack)

To run the Database, Backend, and Frontend locally:

```bash
docker compose -f compose.yaml build
docker compose -f compose.yaml up -d
```

- With this repository’s `compose.yaml`, the UI is typically exposed on **`http://localhost:3000`** (container serves the built frontend).
- For Vite’s dev server (`npm run dev` inside `frontend/`), use **`http://localhost:5173`** instead.
- API interactive docs: **`http://localhost:8000/docs`**

### ROS 2 bridge (optional local testing)

See **`TELEMETRY_README.md`** for ROS 2 Humble, `colcon build`, and `ros2 launch` instructions. Set **`BACKEND_BASE_URL`** in `.env.telemetry` to the running API (e.g. `ws://localhost:8000`).

### Database Management

On startup, SQLAlchemy automatically generates the required tables (`create_all`). To clear the database for testing:

```bash
docker compose down -v
docker compose up -d
```

---

## 8. Deployment Information

The production environment is hosted on DigitalOcean.

- **Live Dashboard:** [Insert URL]
- **Backend API Base:** [Insert URL]
- **Deployment Mechanism:** We utilize GitHub Actions for CI/CD. Pushing to the `prod` branch triggers a workflow that builds the updated Docker images, pushes them to the registry, and executes a `docker service update` command via SSH to our Swarm manager node.

---

## 9. Individual Contributions

- **Hassan Mahdi:** Led the frontend development. Designed the React component architecture, implemented the WebSocket client for real-time data ingestion, and built the UI layout. *(See Git history under `frontend/`.)*
- **Yulong Sheng:** Architected the FastAPI backend. Developed the REST endpoints for session retrieval, designed the SQLAlchemy database models, and handled the server-side WebSocket broadcasting logic. *(See Git history under `backend/`.)*
- **Yamoah Attafuah:** Managed Cloud Ops. Wrote the Dockerfiles, configured the `compose.yaml` for Swarm deployment, set up the DigitalOcean infrastructure, and implemented the GitHub Actions CI/CD pipeline. *(See Git history in the repository root and `.github/`.)*
- **Samson Ajadalu:** Developed the robotics telemetry bridge. Wrote the Python nodes in ROS 2 to extract data from Gazebo/TurtleBot3 and stream them to the cloud backend. Drafted the integration contracts in **`TELEMETRY_README.md`**. *(See Git history under `src/robot_bridge/`.)*

---

## 10. AI Assistance & Verification (Summary)

AI tools were utilized primarily as a technical sounding board and debugging assistant during development.

- **Where AI contributed:** Effective for exploring Docker configuration options and troubleshooting ROS 2 environment errors (for example, Gazebo or client stability issues).
- **Verification:** All AI-suggested changes were validated through local runs, integration tests where applicable, and deployment checks before merge.

For detailed examples of AI interactions, including a representative mistake or limitation, see **`ai-session.md`** in the repository root.

---

## 11. Lessons Learned

This project provided invaluable experience in full-stack cloud orchestration. The biggest technical hurdle was ensuring the reliability of WebSockets across a distributed Docker Swarm. We learned that while WebSockets are excellent for real-time local data, maintaining persistent connections through cloud load balancers requires careful configuration of timeouts and reconnect logic. Additionally, transitioning from local `docker compose` to a cloud Swarm highlighted the importance of environment variables and strict network isolation. Ultimately, we achieved our goal of building a robust bridge between local robotic hardware and cloud infrastructure.
