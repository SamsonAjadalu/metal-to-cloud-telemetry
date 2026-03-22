from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime
import os

# Use environment variable for database URL, fallback to local default if not found.
# Note: In Docker Swarm/Compose, the host should be the database service name (e.g., 'db' or 'postgres').
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://robot_admin:secret_password@db:5432/metal_to_cloud"
)

# Initialize SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for declarative class definitions
Base = declarative_base()

# Database Models (Tables)
class Telemetry(Base):
    __tablename__ = "telemetries"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Identifiers & Metadata
    robot_id = Column(String, index=True)      
    map_id = Column(String, index=True)         
    session_id = Column(String, index=True)     
    
    # Timestamp (Defaults to server's current UTC time when saved)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Robot Pose (Position and Orientation)
    pose_x = Column(Float)
    pose_y = Column(Float)
    yaw = Column(Float)
    
    # Robot Velocity and Diagnostics
    linear_x = Column(Float)
    angular_z = Column(Float)
    battery = Column(Float)


# Fleet tracking — persists across container restarts
class Robot(Base):
    __tablename__ = "robots"

    robot_id = Column(String, primary_key=True)           # e.g. "tb3_001"
    status = Column(String, default="OFFLINE")             # ONLINE / OFFLINE
    battery = Column(Float, default=0.0)
    last_x = Column(Float, default=0.0)                   # last known position
    last_y = Column(Float, default=0.0)
    total_distance_m = Column(Float, default=0.0)          # cumulative distance in meters
    last_seen = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)