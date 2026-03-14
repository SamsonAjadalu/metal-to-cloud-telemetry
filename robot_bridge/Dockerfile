FROM osrf/ros:humble-desktop

RUN apt-get update && apt-get install -y python3-pip

WORKDIR /ros2_ws

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src/robot_bridge ./src/robot_bridge

RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build"

CMD ["/bin/bash", "-c", "source /opt/ros/humble/setup.bash && source /ros2_ws/install/setup.bash && ros2 run robot_bridge telemetry_bridge"]