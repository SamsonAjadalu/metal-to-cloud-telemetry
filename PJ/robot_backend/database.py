from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://robot_admin:secret_password@localhost:5432/metal_to_cloud")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Mission(Base):
    __tablename__ = "missions"
    id = Column(Integer, primary_key=True, index=True)
    robot_name = Column(String, index=True)
    status = Column(String, default="active")
    start_time = Column(DateTime, default=datetime.datetime.utcnow)

class Telemetry(Base):
    __tablename__ = "telemetries"
    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    pose_x = Column(Float)
    pose_y = Column(Float)
    battery = Column(Float)