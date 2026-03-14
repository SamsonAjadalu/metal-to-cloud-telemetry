# Backend API & WebSocket Router

This directory contains the FastAPI backend and database architecture for the "Metal-to-Cloud" telemetry system. It acts as the central high-speed message broker, routing real-time traffic between the React dashboard and the robotic fleet, while efficiently persisting historical data to PostgreSQL.

## Backend Structure

The backend is designed for high concurrency and is modularized into the following core components:

* `main.py`: The FastAPI application, containing the ConnectionManager for precise WebSocket routing and an asynchronous Batch Insert Engine to handle massive load spikes.
* `database.py`: SQLAlchemy ORM configurations and strictly defined table schemas (e.g., telemetries).
* `test_1000_robots.py`: A local load-testing script capable of simulating 1,000 concurrent robot connections to validate system scalability.
* `Dockerfile`: A multi-stage, lightweight container definition for the Python environment.

## How to Run the Backend (for Local Development)

### Set up Environment Variables
The backend relies on the master `compose.yaml` to inject the database credentials. Ensure your local `.env` matches the agreed-upon PostgreSQL variables. The backend will automatically construct the following connection string internally:


DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:${DB_PORT}/${DB_NAME}

### Access the Services
Once the master `docker compose up --build` finishes booting up and the database healthcheck passes, the backend services will be available:

* **Backend API Docs (Swagger UI):** http://localhost:8000/docs
* **Frontend WebSocket Entry:** `ws://localhost:8000/ws/frontend`
* **Robot WebSocket Entry:** `ws://localhost:8000/ws/robot/{robot_id}`

## Section-Specific Guides

### For Frontend
* **Data Flow:** The backend acts as a pure pass-through router. It will not mutate the command or goal payloads. As long as your UI sends the exact JSON schema defined in your ApiService, the backend will route it instantly to the correct robot_id.
* **Map Handling:** The backend only stores and forwards the map_id (e.g., "map_01") as a string within the JSON payload. The dashboard should use this string to fetch the actual .png map from the cloud bucket provided by DevOps.

### For Telemetry (Robot Bridge)
* **Performance & Load Testing:** The backend has been load-tested to successfully support 1,000 concurrent robot connections. To prevent database deadlocks, incoming telemetry is buffered in memory and bulk-inserted into PostgreSQL every second. You can blast data at the WebSocket endpoint without throttling.
* **Map Files:** To maintain high-speed routing, the backend does not serve .yaml or .pgm binary map files. The robot bridge/Nav2 node must fetch these navigation files directly from the DevOps cloud bucket using the map_id string provided in the telemetry loop.

### For DevOps
* **Containerization:** The backend Dockerfile uses python:3.10-slim and implements strict layer caching for requirements.txt to speed up CI/CD pipeline builds.
* **Logging:** The PYTHONUNBUFFERED=1 environment variable is set in the Dockerfile to ensure real-time log streaming (e.g., batch insert notifications) directly to the Docker daemon.
* **Orchestration:** The backend container strictly relies on the PostgreSQL condition: service_healthy check in compose.yaml to ensure the database is fully initialized before the FastAPI server boots.
