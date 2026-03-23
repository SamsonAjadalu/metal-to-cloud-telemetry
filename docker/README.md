# Docker: `stack_sim_nav2` on a VPS

This wraps your existing launch file; **no changes** to `robot_bridge` Python/launch code are required.

## Build

From the **repository root** (parent of `src/`):

```bash
docker build -f docker/Dockerfile -t metal-stack-sim .
```

## Run (headless — typical server)

Uses `network_mode: host` and `privileged: true` (common for Gazebo).

```bash
docker run --rm -it --network host --privileged --shm-size=2g metal-stack-sim
```

The container **default command** is:

`ros2 launch robot_bridge stack_sim_nav2.launch.py headless:=true use_rviz:=false`

### Override launch args

```bash
docker run --rm -it --network host --privileged --shm-size=2g metal-stack-sim \
  ros2 launch robot_bridge stack_sim_nav2.launch.py headless:=true use_rviz:=false count:=3
```

### Interactive shell (then you run launch yourself)

```bash
docker run --rm -it --network host --privileged --shm-size=2g metal-stack-sim bash
source /opt/ros/humble/setup.bash
source /ros_ws/install/setup.bash
ros2 launch robot_bridge stack_sim_nav2.launch.py
```

## Compose

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Gazebo GUI in a web browser

Gazebo does not ship a built-in “web viewer.” This image uses **TigerVNC + noVNC**: you open a normal browser to port **6080** and see the virtual desktop where **gzclient** runs.

```bash
docker run --rm -it --network host --privileged --shm-size=2g \
  -e USE_WEB_GUI=1 \
  -e VNC_PASSWORD=yourpassword \
  metal-stack-sim
```

Then visit `http://<VPS-IP>:6080` and connect with the VNC password.

Or with Compose:

```bash
VNC_PASSWORD=yourpassword docker compose -f docker/docker-compose.yml --profile web-gui up --build
```

**Security:** do not expose `6080` publicly without a VPN, SSH tunnel, or reverse proxy + auth. Default password is weak.

**Performance:** software OpenGL inside Docker is slower than a real GPU desktop.

## Notes

- **Linux + host networking** is the least painful setup for ROS 2 DDS. On macOS/Windows Docker Desktop, host networking behaves differently; use a Linux VPS for this stack.
- Open firewall only for ports your team needs (e.g. backend HTTP), not the whole ROS graph.
