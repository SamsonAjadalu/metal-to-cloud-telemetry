How to Interact with the Backend TODAY (Current State)
The foundational backend is live. Here is exactly how the team can use and test it right now, before we even connect the real robot or frontend UI.

Step 1: Spin up the Backend (For Everyone)
Pull my code and run this in your terminal:

Bash
docker-compose up -d --build
docker-compose restart api
(This starts the FastAPI server and the PostgreSQL database in the background.)

Step 2: Test the REST APIs & Database (Especially for Person A - Frontend)
You don't need Postman or any frontend code to test the database. FastAPI provides a built-in interactive dashboard.

Go to  http://localhost:8000/docs

Create a Mission: Click POST /missions/ -> Try it out. Type a robot name (e.g., "Wall-E") and click Execute. You will see the database assign it a mission_id (e.g., 1).

Save Telemetry: Click POST /telemetry/ -> Try it out. Enter the mission_id you just got, plus some dummy coordinates (x: 10.5, y: 20.1). Click Execute.

Result: The data is now permanently saved in the local PostgreSQL database!

Step 3: Test the WebSocket Connection (Especially for Person D - Sim/Telemetry)
Currently, I have set up a basic Echo WebSocket at /ws/telemetry to verify the connection is working.

If you have a simple WebSocket client (or a Python test script), connect to ws://localhost:8000/ws/telemetry.

Send any JSON payload or text message.

Result: The backend will instantly catch it and echo it back to you: Server Echo: <your_message>.
(Note: In Week 2, this will be upgraded to the ConnectionManager to route traffic properly based on robot_id and the frontend endpoint).

Step 4: DevOps Review (Especially for Person C - DevOps)
The docker-compose.yml and Dockerfile are fully configured with a named volume (pg_data) for state persistence. It is ready for your review and Swarm integration.
