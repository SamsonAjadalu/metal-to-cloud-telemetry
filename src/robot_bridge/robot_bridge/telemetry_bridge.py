import asyncio
import json
import math
import queue
import threading
from datetime import datetime, timezone

import rclpy
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.parameter import Parameter
import websockets
import os


def _default_goal_pose_topic(cmd_vel_topic: str) -> str:
    """e.g. /tb3_001/cmd_vel -> /tb3_001/goal_pose"""
    suf = "/cmd_vel"
    if cmd_vel_topic.endswith(suf):
        return cmd_vel_topic[: -len(suf)] + "/goal_pose"
    return "/goal_pose"


class TelemetryBridge(Node):
    def __init__(self):
        use_sim = os.getenv("USE_SIM_TIME", "").lower() in ("1", "true", "yes")
        super().__init__(
            "telemetry_bridge",
            parameter_overrides=[Parameter("use_sim_time", value=use_sim)],
        )

        self.robot_id = os.getenv("ROBOT_ID", "tb3_001")
        self.map_id = os.getenv("MAP_ID", "map_01")
        self.odom_topic = os.getenv("ODOM_TOPIC", "/odom")
        self.cmd_vel_topic = os.getenv("CMD_VEL_TOPIC", "/cmd_vel")
        self.goal_pose_topic = os.getenv(
            "GOAL_POSE_TOPIC",
            _default_goal_pose_topic(self.cmd_vel_topic),
        )
        self.goal_frame_id = os.getenv("GOAL_FRAME_ID", "map")
        self.session_id = (
            f"session_{self.robot_id}_"
            f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        )

        self.backend_ws_url = f"ws://159.203.4.11:8000/ws/robot/{self.robot_id}"

        self.get_logger().info(f"Robot ID: {self.robot_id}")
        self.get_logger().info(f"Map ID: {self.map_id}")
        self.get_logger().info(f"Odometry Topic: {self.odom_topic}")
        self.get_logger().info(f"Cmd Vel Topic: {self.cmd_vel_topic}")
        self.get_logger().info(f"Goal Pose Topic: {self.goal_pose_topic}")
        self.get_logger().info(f"Goal frame_id: {self.goal_frame_id}")
        self.get_logger().info(f"Session ID: {self.session_id}")
        self.get_logger().info(f"Backend WebSocket URL: {self.backend_ws_url}")

        # ROS -> bridge
        self.odom_sub = self.create_subscription(
            Odometry,
            self.odom_topic,
            self.odom_callback,
            10
        )

        # bridge -> ROS
        self.cmd_vel_pub = self.create_publisher(
            Twist,
            self.cmd_vel_topic,
            10
        )
        self.goal_pose_pub = self.create_publisher(
            PoseStamped,
            self.goal_pose_topic,
            10,
        )

        # Telemetry queue for websocket sender thread
        self.telemetry_queue: queue.Queue[dict] = queue.Queue(maxsize=200)

        # Stop flag
        self._stop_event = threading.Event()

        # Start websocket worker in background thread
        self.ws_thread = threading.Thread(
            target=self._start_ws_worker,
            daemon=True
        )
        self.ws_thread.start()

    def odom_callback(self, msg: Odometry):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y

        q = msg.pose.pose.orientation
        yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        )

        linear_x = msg.twist.twist.linear.x
        angular_z = msg.twist.twist.angular.z

        telemetry = {
            "type": "telemetry",
            "robot_id": self.robot_id,
            "map_id": self.map_id,
            "session_id": self.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "x": x,
            "y": y,
            "yaw": yaw,
            "linear_x": linear_x,
            "angular_z": angular_z,
            "battery": self._simulate_battery_level(),
        }

        self._enqueue_telemetry(telemetry)

    def _simulate_battery_level(self) -> float:
        now = datetime.now(timezone.utc)
        seconds_since_midnight = (
            now.hour * 3600
            + now.minute * 60
            + now.second
        )
        day_progress = seconds_since_midnight / 86400.0

        battery_level = 85.0 + 10.0 * math.sin(2.0 * math.pi * day_progress)
        return round(max(0.0, min(100.0, battery_level)), 1)

    def _enqueue_telemetry(self, telemetry: dict):
        try:
            self.telemetry_queue.put_nowait(telemetry)
        except queue.Full:
            try:
                _ = self.telemetry_queue.get_nowait()
            except queue.Empty:
                pass

            try:
                self.telemetry_queue.put_nowait(telemetry)
            except queue.Full:
                pass

    def send_velocity_command(self, linear_x: float, angular_z: float):
        msg = Twist()
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        self.cmd_vel_pub.publish(msg)

        self.get_logger().info(
            f"Published {self.cmd_vel_topic} -> linear_x={linear_x}, angular_z={angular_z}"
        )

    def handle_backend_command(self, command: dict):
        """
        command: type command -> Twist on cmd_vel
        goal: type goal -> PoseStamped on goal_pose (Nav2)
        """
        msg_type = command.get("type")
        if msg_type == "command":
            self._handle_velocity_command(command)
        elif msg_type == "goal":
            self._handle_nav_goal(command)
        else:
            self.get_logger().warn(f"Ignoring message type={msg_type!r}: {command}")

    def _handle_velocity_command(self, command: dict):
        robot_id = command.get("robot_id")
        if robot_id != self.robot_id:
            self.get_logger().info(
                f"Ignoring command for robot_id={robot_id}"
            )
            return

        linear_x = float(command.get("linear_x_cmd", 0.0))
        angular_z = float(command.get("angular_z_cmd", 0.0))

        self.get_logger().info(
            f"Received backend command from {self.backend_ws_url}: {command}"
        )

        self.send_velocity_command(linear_x, angular_z)

    def _handle_nav_goal(self, command: dict):
        robot_id = command.get("robot_id")
        if robot_id != self.robot_id:
            self.get_logger().info(
                f"Ignoring goal for robot_id={robot_id}"
            )
            return

        x = float(command.get("x", 0.0))
        y = float(command.get("y", 0.0))
        yaw = float(command.get("yaw", 0.0))

        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.goal_frame_id
        msg.pose.position.x = x
        msg.pose.position.y = y
        msg.pose.position.z = 0.0
        half = yaw * 0.5
        msg.pose.orientation.x = 0.0
        msg.pose.orientation.y = 0.0
        msg.pose.orientation.z = math.sin(half)
        msg.pose.orientation.w = math.cos(half)

        self.goal_pose_pub.publish(msg)
        self.get_logger().info(
            f"Published Nav2 goal to {self.goal_pose_topic} "
            f"(frame={self.goal_frame_id}): x={x}, y={y}, yaw={yaw}"
        )

    def _start_ws_worker(self):
        asyncio.run(self._websocket_loop())

    async def _websocket_loop(self):
        while not self._stop_event.is_set():
            try:
                self.get_logger().info(
                    f"Connecting to backend WebSocket: {self.backend_ws_url}"
                )

                async with websockets.connect(self.backend_ws_url) as websocket:
                    self.get_logger().info("Connected to backend WebSocket")

                    sender_task = asyncio.create_task(
                        self._sender_loop(websocket)
                    )
                    receiver_task = asyncio.create_task(
                        self._receiver_loop(websocket)
                    )

                    done, pending = await asyncio.wait(
                        [sender_task, receiver_task],
                        return_when=asyncio.FIRST_EXCEPTION
                    )

                    for task in pending:
                        task.cancel()

                    for task in done:
                        exc = task.exception()
                        if exc:
                            raise exc

            except Exception as e:
                self.get_logger().error(
                    f"WebSocket connection error: {e}. Reconnecting in 2 seconds..."
                )
                await asyncio.sleep(2.0)

    async def _sender_loop(self, websocket):
        while not self._stop_event.is_set():
            try:
                telemetry = self.telemetry_queue.get_nowait()
            except queue.Empty:
                await asyncio.sleep(0.05)
                continue

            message = json.dumps(telemetry)
            await websocket.send(message)

    async def _receiver_loop(self, websocket):
        while not self._stop_event.is_set():
            message = await websocket.recv()

            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                self.get_logger().warn(f"Received non-JSON message: {message}")
                continue

            self.handle_backend_command(data)

    def destroy_node(self):
        self._stop_event.set()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = TelemetryBridge()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()