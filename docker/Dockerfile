# ROS 2 Humble + Gazebo + Nav2 + TurtleBot3 + optional noVNC for Gazebo in a browser.
# Build from repo root:
#   docker build -f docker/Dockerfile -t metal-stack-sim .
#
# Run (headless, typical VPS):
#   docker run --rm -it --network host --privileged --shm-size=2g metal-stack-sim
#
# Run with Gazebo GUI in browser (open http://<host>:6080):
#   docker run --rm -it --network host --privileged --shm-size=2g -e USE_WEB_GUI=1 -e VNC_PASSWORD=secret metal-stack-sim

FROM osrf/ros:humble-desktop-full-jammy

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-pip \
    python3-websockets \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-turtlebot3-gazebo \
    ros-humble-turtlebot3-navigation2 \
    ros-humble-gazebo-ros-pkgs \
    tigervnc-standalone-server \
    tigervnc-common \
    novnc \
    websockify \
    openbox \
    dbus-x11 \
    x11-xserver-utils \
    mesa-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ros_ws
COPY src/robot_bridge src/robot_bridge

RUN bash -c "source /opt/ros/humble/setup.bash \
    && colcon build --packages-select robot_bridge --symlink-install"

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /ros_ws
ENTRYPOINT ["/entrypoint.sh"]
CMD []
