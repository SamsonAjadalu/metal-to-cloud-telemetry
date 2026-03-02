# Fleet Telemetry & Control Infrastructure (Metal-to-Cloud)

## 1. Motivation

Robotic systems increasingly rely on cloud services for monitoring, debugging, analytics, and remote intervention. However, many robotics workflows lack a simple cloud-native foundation that supports both real-time telemetry and persistent mission/action history. This project builds a "metal-to-cloud" telemetry and control pipeline for a simulated robot/agent, whereby the agent streams telemetry to the cloud in real time, operators can issue basic commands, and all data on robot mission (action and conditions or state) is persisted for replay and performance analysis.

The target users for this project include robotics developers, test engineers, and operators who need live system visibility plus historical mission playback for debugging and evaluation.

## 2. Objective and Key Features

### Architecture

``` mermaid
flowchart LR
  subgraph K8s[DigitalOcean Kubernetes (DOKS)]
    FE[React Dashboard]
    BE[FastAPI Backend]
    DB[(PostgreSQL\nPVC Persistent Volume)]
    FE <-- "WebSocket (live)" --> BE
    FE <-- "REST (history/sessions)" --> BE
    BE -->|SQL| DB
    DB -->|SQL| BE
  end

  R[Robot/Sim Client\n(Python or ROS2)] <-- "WebSocket (telemetry + commands)" --> BE
```

### Objective
Build and deploy a stateful cloud-native application that provides:

- Real-time telemetry streaming from an autonomous agent,
- Persistent storage of mission history, and
- A web dashboard for live monitoring, replay, and basic command/control.

### Key Features (Demo-facing Components)

- **Live monitoring:** Dashboard displays pose, battery, and diagnostics with near real-time updates.
- **Command/control:** User sends commands (e-stop, mode switch, simple motion commands) that the agent receives immediately.
- **Replay & analytics:** User selects a prior mission session and replays the robot path and time-series metrics (e.g., battery vs time, error events).

### Core System Components (Implementation-facing Components)

- **Robot/Sim Client:** Python script or ROS2 node producing telemetry and consuming commands.
- **Backend (FastAPI):**
  - WebSocket channel for bi-directional telemetry + command/control (Advanced Feature #1).
  - REST APIs for querying sessions, history, and summary stats.
- **PostgreSQL + Persistent Volume:** stores telemetry + command history for replay and state continuity.
- **React Dashboard:** live views + replay views.

### Planned Advanced Features

1. **Real-time functionality:** A WebSocket channel enabling bi-directional telemetry streaming and low-latency command/control between the agent, backend, and dashboard.

2. **CI/CD pipeline:** A GitHub Actions workflow to automatically build Docker images and deploy updates to the production DigitalOcean Docker Swarm cluster.

## 3. Tentative Plan

### Week 1 (Foundation)
- Define telemetry schema + DB schema (missions/sessions, telemetry points, commands).
- Scaffold FastAPI backend (REST + basic WebSocket endpoint).
- Scaffold React dashboard (live telemetry page).
- Local Docker Compose stack (API + DB + frontend).

### Week 2 (Real-time + Persistence)
- End-to-end WebSocket streaming (agent → backend → dashboard).
- Persist telemetry and commands to PostgreSQL.
- Implement basic command/control loop.

### Week 3 (Replay + Analytics)
- Replay UI: session selector + path replay + basic charts.
- REST endpoints for historical queries and summary statistics.

### Week 4 (Docker Swarm Local Validation)
- Move services to a docker-compose.yml stack file configured for Swarm mode.
- Configure PostgreSQL persistence using Docker named volumes mapped to the local host.
- Validate service replication and internal overlay network routing for stateless components.

### Week 5 (Cloud Deployment)
- Provision DigitalOcean Droplets and initialize a Docker Swarm cluster (manager/worker nodes).
- Deploy the stack to the cloud Swarm cluster and configure persistent block storage for PostgreSQL.
- Set up monitoring/alerts using DigitalOcean tooling.

### Week 6 (CI/CD + Polish)
- GitHub Actions pipeline to build images and deploy to Docker Swarm cluster (Advanced Feature #2).
- Final demo polish and documentation.

### Responsibilities Split
1. Frontend (React) - Hassan Mahdi
2. Backend (FastAPI + WS + REST) - Yulong Sheng
3. DevOps (Docker + Docker Swarm + DO + CI/CD) - Yamoah Attafuah
4. Telemetry Client + Schema + Replay Data Design - Samson Ajadalu

## 4. Initial Independent Reasoning (Before Using AI)

Before using any AI tools, we decided on DigitalOcean + Docker Swarm, WebSockets for real-time, Postgres for data persistence, and data replay as one of the project's key features. We chose Docker Swarm over Kubernetes because of its native integration with Docker Compose, allowing us to focus more on the application logic and WebSocket infrastructure rather than the orchestration overhead. We expect challenges in ensuring the reliability of WebSocket connections, managing persistent state for Postgres across Swarm nodes, and setting up the CI/CD pipeline.

## 5. AI Assistance Disclosure

AI was used only for wording polish. All the architecture and feature decisions were made by the team, the process of which is explained as follows:

* Unassisted Work: The core project concept (the Metal-to-Cloud pipeline), the target user definition, the selection of the primary tech stack (FastAPI, React, PostgreSQL), and the choice of advanced features (WebSockets and CI/CD) were all developed completely independently by the team.

* AI-Assisted Tasks: AI was used to refine the proposal's wording and to sanity check that the file's Markdown formatting and sections aligned correctly with the grading rubric.
