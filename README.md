# Metal-to-Cloud Backend Infrastructure

This repository contains the backend infrastructure for the **Fleet Telemetry & Control Infrastructure (Metal-to-Cloud)** project. 

It provides the core stateful cloud-native application, handling real-time bi-directional communication via WebSockets and persistent mission data storage using PostgreSQL. This backend serves as the central message broker between the ROS 2 TurtleBot3 simulation (Agent) and the React Dashboard (Operator).



##  Architecture Overview

```mermaid
flowchart LR
  subgraph Swarm[DigitalOcean Docker Swarm]
    FE[React Dashboard]
    BE[FastAPI Backend]
    DB[(PostgreSQL Named Volume)]
    FE <-- WebSocket live --> BE
    FE <-- REST history/sessions --> BE
    BE -->|SQL| DB
    DB -->|SQL| BE
  end
  R[Robot/Sim Client] <-- WebSocket telemetry + commands --> BE
