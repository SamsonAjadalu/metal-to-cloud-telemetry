from fastapi import FastAPI, Depends, WebSocket
from sqlalchemy.orm import Session
import database

# 让数据库建表
database.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Metal-to-Cloud API")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 接口1：检查系统是否存活
@app.get("/status")
def check_status():
    return {"message": "Backend is running!"}

# 接口2：创建一个新任务
@app.post("/missions/")
def create_mission(robot_name: str, db: Session = Depends(get_db)):
    new_mission = database.Mission(robot_name=robot_name)
    db.add(new_mission)
    db.commit()
    db.refresh(new_mission)
    return {"message": "Mission started!", "mission_id": new_mission.id}

# 接口3：接收机器人数据并存入数据库
@app.post("/telemetry/")
def save_telemetry(mission_id: int, x: float, y: float, battery: float, db: Session = Depends(get_db)):
    new_data = database.Telemetry(mission_id=mission_id, pose_x=x, pose_y=y, battery=battery)
    db.add(new_data)
    db.commit()
    return {"status": "success", "saved_data": {"x": x, "y": y, "battery": battery}}

# WebSocket 对讲机通道
@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Server Echo: {data}")
    except Exception:
        print("WebSocket Disconnected")