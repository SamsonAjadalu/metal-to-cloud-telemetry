# Fleet Telemetry & Control Infrastructure (Metal-to-Cloud)

## 1. Motivation

Robotic systems increasingly rely on cloud services for monitoring, debugging, analytics, and remote intervention. However, many robotics workflows lack a simple, cloud-native foundation that supports both real-time telemetry and persistent mission history. This project builds a "metal-to-cloud" telemetry and control pipeline for a simulated robot/agent: the agent streams telemetry to the cloud in real time, operators can issue basic commands, and all mission data is persisted for replay and performance analysis.

**Target users:** robotics developers, test engineers, and operators who need live system visibility plus historical mission playback for debugging and evaluation.

## 2. Objective and Key Features

### Objective
Build and deploy a stateful cloud-native application that provides:

- real-time telemetry streaming from an autonomous agent,
- persistent storage of mission history, and
- a web dashboard for live monitoring, replay, and basic command/control.

### Key features (demo-facing)

- **Live monitoring:** Dashboard displays pose, battery, and diagnostics with near real-time updates.
- **Command/control:** User sends commands (e-stop, mode switch, simple motion commands) that the agent receives immediately.
- **Replay & analytics:** User selects a prior mission session and replays the robot path and time-series metrics (e.g., battery vs time, error events).

### Core system components (implementation-facing)

- **Robot/Sim client:** Python script or ROS2 node producing telemetry and consuming commands.
- **Backend (FastAPI):**
  - WebSocket channel for bi-directional telemetry + command/control (Advanced Feature #1).
  - REST APIs for querying sessions, history, and summary stats.
- **PostgreSQL + persistent volume:** stores telemetry + command history for replay and state continuity.
- **React dashboard:** live views + replay views.

## 3. Tentative Plan

### Week 1 (Foundation)
- Define telemetry schema + DB schema (missions/sessions, telemetry points, commands).
- Scaffold FastAPI backend (REST + basic WebSocket endpoint).
- Scaffold React dashboard (live telemetry page).
- Local Docker Compose stack (api + db + frontend).

### Week 2 (Real-time + persistence)
- End-to-end WebSocket streaming (agent → backend → dashboard).
- Persist telemetry and commands to PostgreSQL.
- Implement basic command/control loop.

### Week 3 (Replay + analytics)
- Replay UI: session selector + path replay + basic charts.
- REST endpoints for historical queries and summary statistics.

### Week 4 (Kubernetes local validation)
- Move services to Kubernetes manifests on minikube.
- Configure PostgreSQL with a PersistentVolumeClaim.
- Validate replication/service routing for stateless components.

### Week 5 (Cloud deployment)
- Deploy to DigitalOcean Kubernetes (DOKS).
- Configure persistent storage for PostgreSQL.
- Set up monitoring/alerts using DigitalOcean tooling.

### Week 6 (CI/CD + polish)
- GitHub Actions pipeline to build images and deploy to Kubernetes (Advanced Feature #2).
- Final demo polish and documentation.

## 4. Initial Independent Reasoning (Before Using AI)

Before using any AI tools, we decided on DigitalOcean + Kubernetes, WebSockets for real-time, Postgres for persistence, and replay as the main differentiator. We expected challenges in WS reliability + PV for Postgres + CI/CD.

## 5. AI Assistance Disclosure

AI was used only for wording polish. Architecture and feature decisions were made by the team.
