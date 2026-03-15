# Fleet Telemetry & Control Frontend

Welcome to the React Frontend for the Fleet Telemetry system. This project was initialized using Vite + React + TypeScript and designed to seamlessly interface with the backend and telemetry services.

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
