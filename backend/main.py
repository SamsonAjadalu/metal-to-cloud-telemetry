from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict
import database
import asyncio
import math
import datetime

# Create database tables (based on the latest database.py schema)
database.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Metal-to-Cloud API")

# CORS: allow the frontend (different origin in local dev) to call REST endpoints
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# 1. Data Payload Models (Pydantic) 

class TelemetryPayload(BaseModel):
    type: str
    robot_id: str
    map_id: str
    session_id: str
    timestamp: str
    x: float
    y: float
    yaw: float
    linear_x: float
    angular_z: float
    battery: float

class CommandPayload(BaseModel):
    type: str
    robot_id: str
    linear_x_cmd: float
    angular_z_cmd: float

class GoalPayload(BaseModel):
    type: str
    robot_id: str
    x: float
    y: float
    yaw: float

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 2. Core Brain: WebSocket Connection Manager

class ConnectionManager:
    def __init__(self):
        # Store the single frontend connection
        self.frontend_ws: WebSocket = None
        # Store all active robot connections, format: {"tb3_01": WebSocket, ...}
        self.active_robots: Dict[str, WebSocket] = {}

    async def connect_frontend(self, ws: WebSocket):
        await ws.accept()
        self.frontend_ws = ws
        print("🟢 Frontend connected!")

    async def connect_robot(self, ws: WebSocket, robot_id: str):
        await ws.accept()
        self.active_robots[robot_id] = ws
        print(f"🟢 Robot [{robot_id}] connected!")

    def disconnect_frontend(self):
        self.frontend_ws = None
        print("🔴 Frontend disconnected.")

    def disconnect_robot(self, robot_id: str):
        if robot_id in self.active_robots:
            del self.active_robots[robot_id]
            print(f"🔴 Robot [{robot_id}] disconnected.")

    async def send_to_frontend(self, message: dict):
        # Forward the received data as-is to the frontend, if connected
        if self.frontend_ws:
            await self.frontend_ws.send_json(message)

    async def send_to_robot(self, robot_id: str, message: dict):
        # Look up the robot in the dictionary and send the message
        if robot_id in self.active_robots:
            ws = self.active_robots[robot_id]
            await ws.send_json(message)
        else:
            print(f"⚠️ Cannot send. Robot [{robot_id}] is offline.")

# Instantiate the connection manager
manager = ConnectionManager()

# High-Concurrency Engine: Batch Insert
# ==========================================
# This is the global in-memory buffer
telemetry_buffer = []

async def batch_save_to_db():
    """A background infinite loop that empties the buffer and saves to the DB every second."""
    while True:
        await asyncio.sleep(1)  # Strictly control the frequency: trigger once per second
        
        if len(telemetry_buffer) > 0:
            # 1. Instantly copy the data from the buffer and clear it so clients can keep appending
            data_to_save = telemetry_buffer.copy()
            telemetry_buffer.clear()
            
            # 2. Open the database session once and use SQLAlchemy for a lightning-fast bulk insert
            db = database.SessionLocal()
            try:
                # bulk_insert_mappings is extremely efficient; it converts the list into a single massive SQL insert
                db.bulk_insert_mappings(database.Telemetry, data_to_save)
                db.commit()
                print(f"💾 [Batch Insert] Saved {len(data_to_save)} records to DB at once!")
            except Exception as e:
                db.rollback()
                print(f"❌ [DB Error] Failed to save batch: {e}")
            finally:
                db.close() # Always remember to close the database session

# When the FastAPI server starts, automatically spawn this background worker
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(batch_save_to_db())
    print("🚀 Background batch writer started!")

# 3. REST APIs (For local testing, frontend replay, and fleet overview)

@app.get("/status")
def check_status():
    return {"message": "Backend is running and routing traffic!"}


@app.get("/api/fleet")
def get_fleet(db: Session = Depends(get_db)):
    """Return all known robots with their persistent stats (survives container restarts)."""
    robots = db.query(database.Robot).order_by(database.Robot.robot_id).all()
    now = datetime.datetime.utcnow()
    fleet = []
    for r in robots:
        last_seen_ago = (now - r.last_seen).total_seconds() if r.last_seen else None
        # Consider robot offline if not seen for 15+ seconds
        effective_status = "ONLINE" if last_seen_ago is not None and last_seen_ago < 15 else "OFFLINE"
        fleet.append({
            "robot_id": r.robot_id,
            "status": effective_status,
            "battery": round(r.battery, 1) if r.battery else 0.0,
            "x": round(r.last_x, 2) if r.last_x else 0.0,
            "y": round(r.last_y, 2) if r.last_y else 0.0,
            "total_distance_m": round(r.total_distance_m, 2) if r.total_distance_m else 0.0,
            "last_seen": r.last_seen.isoformat() if r.last_seen else None,
            "last_seen_ago_s": round(last_seen_ago, 1) if last_seen_ago is not None else None,
        })
    return fleet

@app.post("/telemetry/")
def save_telemetry(data: TelemetryPayload, db: Session = Depends(get_db)):
    # Receive the full payload and save it to the database
    new_data = database.Telemetry(
        robot_id=data.robot_id,
        map_id=data.map_id,
        session_id=data.session_id,
        pose_x=data.x,
        pose_y=data.y,
        yaw=data.yaw,
        linear_x=data.linear_x,
        angular_z=data.angular_z,
        battery=data.battery
    )
    db.add(new_data)
    db.commit()
    return {"status": "success", "saved_robot": data.robot_id}



# Replay Endpoints (Historical Data for UI)


@app.get("/sessions")
def get_all_sessions(db: Session = Depends(get_db)):
    """Fetch a list of all unique session IDs from the database."""
    # Query all distinct session_ids
    sessions = db.query(database.Telemetry.session_id).distinct().all()
    # Clean up the list of tuples into a simple list of strings
    return {"sessions": [s[0] for s in sessions if s[0] is not None]}

@app.get("/sessions/{session_id}")
def get_session_history(session_id: str, db: Session = Depends(get_db)):
    """Fetch the complete telemetry history for a specific session for UI playback."""
    # Utilizing the index=True we set in database.py for lightning-fast queries,
    # and sorting the results chronologically by timestamp
    history = db.query(database.Telemetry).filter(
        database.Telemetry.session_id == session_id
    ).order_by(database.Telemetry.timestamp.asc()).all()
    
    # NEW SAFEGUARD
    safe_data = []
    for row in history:
        safe_data.append({
            "robot_id": row.robot_id,
            "map_id": row.map_id,
            "session_id": row.session_id,
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            "x": row.pose_x,
            "y": row.pose_y,
            "yaw": row.yaw,
            "linear_x": row.linear_x,
            "angular_z": row.angular_z,
            "battery": row.battery
        })
    
    return {
        "session_id": session_id,
        "total_records": len(safe_data),
        "data": safe_data
    }

# 4. WebSocket Routing Endpoints (The actual traffic hub)


# Endpoint A: Dedicated connection for the Frontend
@app.websocket("/ws/frontend")
async def frontend_endpoint(websocket: WebSocket):
    await manager.connect_frontend(websocket)
    try:
        while True:
            # Receive commands or goals from the frontend
            data = await websocket.receive_json()
            
            # 🌟 NEW: Basic format validation to ensure incoming commands are structurally sound
            if "type" not in data or "robot_id" not in data:
                await websocket.send_json({"error": "Invalid format. Missing 'type' or 'robot_id'"})
                continue # Skip routing this malformed message
                
            robot_id = data.get("robot_id")
            
            # The manager checks the robot_id and routes it precisely!
            if robot_id:
                await manager.send_to_robot(robot_id, data)
    except WebSocketDisconnect:
        manager.disconnect_frontend()


# Endpoint B: Dedicated connection for all Robots
@app.websocket("/ws/robot/{robot_id}")
async def robot_endpoint(websocket: WebSocket, robot_id: str):
    await manager.connect_robot(websocket, robot_id)
    try:
        while True:
            # 1. Receive real-time telemetry from the robot
            data = await websocket.receive_json()

            data["robot_id"] = robot_id
            
            # 2. Act as the message router: instantly forward the data to the frontend dashboard
            await manager.send_to_frontend(data)
            
            # 3. High-Concurrency Logic: Format the data for the database and append it to the buffer
            db_item = {
                "robot_id": robot_id,
                "map_id": data.get("map_id"),
                "session_id": data.get("session_id"),
                "pose_x": data.get("x"),
                "pose_y": data.get("y"),
                "yaw": data.get("yaw"),
                "linear_x": data.get("linear_x"),
                "angular_z": data.get("angular_z"),
                "battery": data.get("battery")
            }
            telemetry_buffer.append(db_item)

            # 4. Fleet Tracking: Upsert robot row and calculate incremental distance
            x_new = data.get("x", 0.0)
            y_new = data.get("y", 0.0)
            try:
                db = database.SessionLocal()
                robot = db.query(database.Robot).filter(database.Robot.robot_id == robot_id).first()
                if robot:
                    dx = x_new - (robot.last_x or 0.0)
                    dy = y_new - (robot.last_y or 0.0)
                    dist = math.sqrt(dx * dx + dy * dy)
                    # Only add distance if movement is reasonable (< 5m per tick = not a teleport)
                    if dist < 5.0:
                        robot.total_distance_m = (robot.total_distance_m or 0.0) + dist
                    robot.last_x = x_new
                    robot.last_y = y_new
                    robot.battery = data.get("battery", 0.0)
                    robot.status = "ONLINE"
                    robot.last_seen = datetime.datetime.utcnow()
                else:
                    robot = database.Robot(
                        robot_id=robot_id,
                        status="ONLINE",
                        battery=data.get("battery", 0.0),
                        last_x=x_new,
                        last_y=y_new,
                        total_distance_m=0.0,
                        last_seen=datetime.datetime.utcnow()
                    )
                    db.add(robot)
                db.commit()
            except Exception as e:
                print(f"⚠️ Fleet tracking error: {e}")
            finally:
                db.close()
            
    except WebSocketDisconnect:
        manager.disconnect_robot(robot_id)
        # Mark robot as OFFLINE in the database
        try:
            db = database.SessionLocal()
            robot = db.query(database.Robot).filter(database.Robot.robot_id == robot_id).first()
            if robot:
                robot.status = "OFFLINE"
                db.commit()
        except Exception:
            pass
        finally:
            db.close()
