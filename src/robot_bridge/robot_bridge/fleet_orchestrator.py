import argparse
import copy
import json
import os
import shlex
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from ament_index_python.packages import get_package_share_directory
except ImportError:  # pragma: no cover
    get_package_share_directory = None  # type: ignore[misc, assignment]


def parse_bool(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "on"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--robots-per-world", type=int, default=20)
    parser.add_argument("--headless", type=parse_bool, default=False)
    parser.add_argument("--state-file", default="fleet_state.json")
    parser.add_argument("--backend-url", default="ws://localhost:8000")
    parser.add_argument("--dry-run", type=parse_bool, default=False)
    parser.add_argument(
        "--skip-world-launch",
        action="store_true",
        help=(
            "Do not run turtlebot3_world (avoids a second gzserver). "
            "Use when Gazebo is already up (e.g. stack_sim_nav2.launch.py)."
        ),
    )
    return parser.parse_args()


def load_state(path: Path) -> dict:
    if not path.exists():
        return {
            "next_world_index": 1,
            "next_robot_index": 1,
            "worlds": [],
        }

    with path.open("r", encoding="utf-8") as state_file:
        return json.load(state_file)


def save_state(path: Path, state: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as state_file:
        json.dump(state, state_file, indent=2)


def run_detached(command: str, log_file: Path | None = None) -> bool:
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_handle = log_file.open("a", encoding="utf-8")
        log_handle.write(f"\n$ {command}\n")
    else:
        log_handle = subprocess.DEVNULL

    process = subprocess.Popen(
        ["bash", "-lc", command],
        stdout=log_handle,
        stderr=log_handle,
        start_new_session=True,
    )
    time.sleep(1.0)
    is_running = process.poll() is None

    if log_file is not None and log_handle not in (None, subprocess.DEVNULL):
        log_handle.flush()
        log_handle.close()

    return is_running


def run_blocking(command: str, log_file: Path, timeout_sec: int = 60) -> bool:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as log_handle:
        log_handle.write(f"\n$ {command}\n")
        try:
            result = subprocess.run(
                ["bash", "-lc", command],
                stdout=log_handle,
                stderr=log_handle,
                timeout=timeout_sec,
                check=False,
            )
        except subprocess.TimeoutExpired:
            log_handle.write(
                f"[orchestrator] Command timed out after {timeout_sec}s\n"
            )
            return False

    return result.returncode == 0


def wait_for_service(service_name: str, timeout_sec: int = 20) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        result = subprocess.run(
            ["bash", "-lc", f"ros2 service list | grep -x '{service_name}'"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode == 0:
            return True
        time.sleep(1.0)
    return False


def write_namespaced_tb3_sdf(namespace: str, turtlebot3_model: str, dest: Path) -> None:
    """
    Match turtlebot3_gazebo/launch/multi_robot.launch.py: unique TF frame ids per robot.
    Required so Nav2 under /{namespace}/tf sees {namespace}/odom instead of missing odom.
    """
    if get_package_share_directory is None:
        raise RuntimeError(
            "ament_index_python is required to locate turtlebot3_gazebo; "
            "source your ROS workspace before running fleet_orchestrator."
        )
    share = Path(get_package_share_directory("turtlebot3_gazebo"))
    src = share / "models" / f"turtlebot3_{turtlebot3_model}" / "model.sdf"
    tree = ET.parse(src)
    root = tree.getroot()
    for el in root.iter("odometry_frame"):
        el.text = f"{namespace}/odom"
    for el in root.iter("robot_base_frame"):
        el.text = f"{namespace}/base_footprint"
    for el in root.iter("frame_name"):
        if el.text and el.text.strip() == "base_scan":
            el.text = f"{namespace}/base_scan"
    dest.parent.mkdir(parents=True, exist_ok=True)
    rough = ET.tostring(root, encoding="unicode")
    dest.write_text('<?xml version="1.0" ?>\n' + rough, encoding="utf-8")


def robot_state_publisher_launch_command(namespace: str) -> str:
    model = os.getenv("TURTLEBOT3_MODEL", "burger")
    return (
        f"TURTLEBOT3_MODEL={shlex.quote(model)} "
        "ros2 launch robot_bridge robot_state_publisher_ns.launch.py "
        f"namespace:={shlex.quote(namespace)} use_sim_time:=true"
    )


def fleet_namespaced_sdf_path(logs_dir: Path, robot_id: str) -> Path:
    return logs_dir / "fleet_sdfs" / f"{robot_id}.sdf"


def ensure_fleet_tb3_sdf(
    logs_dir: Path, robot_id: str, namespace: str, *, dry_run: bool
) -> str | None:
    """
    If SPAWN_ROBOT_CMD_TEMPLATE is unset, write a TurtleBot3 SDF with TF frames
    prefixed by namespace (matches turtlebot3_gazebo multi_robot.launch.py).
    """
    if os.getenv("SPAWN_ROBOT_CMD_TEMPLATE"):
        return None
    sdf_p = fleet_namespaced_sdf_path(logs_dir, robot_id)
    if dry_run:
        print(f"[DRY-RUN] Would write namespaced TurtleBot3 SDF to {sdf_p}")
    else:
        write_namespaced_tb3_sdf(
            namespace, os.getenv("TURTLEBOT3_MODEL", "burger"), sdf_p
        )
    return str(sdf_p.resolve())


def world_launch_command(headless: bool, world_name: str) -> str:
    env_template = os.getenv("WORLD_CMD_TEMPLATE")
    if env_template:
        return env_template.format(world_name=world_name, headless=str(headless).lower())

    if headless:
        return "TURTLEBOT3_MODEL=${TURTLEBOT3_MODEL:-burger} ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py gui:=false"

    return "TURTLEBOT3_MODEL=${TURTLEBOT3_MODEL:-burger} ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py"


def spawn_robot_command(
    robot_id: str,
    namespace: str,
    x: float,
    y: float,
    sdf_path: str | None = None,
) -> str:
    env_template = os.getenv("SPAWN_ROBOT_CMD_TEMPLATE")
    if env_template:
        return env_template.format(
            robot_id=robot_id,
            namespace=namespace,
            x=x,
            y=y,
        )

    if sdf_path is not None:
        file_arg = shlex.quote(sdf_path)
    else:
        turtlebot3_model = os.getenv("TURTLEBOT3_MODEL", "burger")
        file_arg = (
            "$(ros2 pkg prefix turtlebot3_gazebo)/share/turtlebot3_gazebo/models/"
            f"turtlebot3_{turtlebot3_model}/model.sdf"
        )

    # Match turtlebot3_gazebo multi_spawn_turtlebot3.launch.py: pass namespace without a
    # leading slash. A leading '/' can confuse plugin/TF naming vs namespaced Nav2.
    return (
        "ros2 run gazebo_ros spawn_entity.py "
        f"-entity {robot_id} "
        f"-file {file_arg} "
        f"-robot_namespace {namespace} "
        f"-x {x:.2f} -y {y:.2f} -z 0.01"
    )


def bridge_command(robot_id: str, map_id: str, namespace: str, backend_url: str) -> str:
    env_template = os.getenv("BRIDGE_CMD_TEMPLATE")
    if env_template:
        return env_template.format(
            robot_id=robot_id,
            map_id=map_id,
            namespace=namespace,
            backend_url=backend_url,
        )

    return (
        f"ROBOT_ID={robot_id} "
        f"MAP_ID={map_id} "
        f"ODOM_TOPIC=/{namespace}/odom "
        f"CMD_VEL_TOPIC=/{namespace}/cmd_vel "
        f"BACKEND_WS_URL={backend_url}/ws/robot/{robot_id} "
        "ros2 run robot_bridge telemetry_bridge"
    )


def make_robot_id(next_robot_index: int) -> str:
    return f"tb3_{next_robot_index:03d}"


def make_world_id(next_world_index: int) -> str:
    return f"map_{next_world_index:02d}"


def allocate_robots(
    count: int,
    state: dict,
    robots_per_world: int,
    headless: bool,
    dry_run: bool,
    backend_url: str,
    logs_dir: Path,
    skip_world_launch: bool = False,
):
    pending = count
    worlds = state["worlds"]

    existing_robot_ids = set()
    for world in worlds:
        existing_robot_ids.update(world["robots"])

    print(f"[fleet] Spawning {count} robot(s). Existing worlds: {len(worlds)}.")

    for world in worlds:
        if pending <= 0:
            break

        capacity = int(world.get("capacity", robots_per_world))
        free_slots = capacity - len(world["robots"])
        if free_slots > 0:
            print(f"[fleet] Filling existing world {world['world_id']} ({free_slots} free slot(s))")
        while pending > 0 and free_slots > 0:
            robot_id = make_robot_id(state["next_robot_index"])
            while robot_id in existing_robot_ids:
                state["next_robot_index"] += 1
                robot_id = make_robot_id(state["next_robot_index"])

            slot_index = len(world["robots"])
            x = (slot_index % 5) * 1.0
            y = (slot_index // 5) * 1.0
            namespace = robot_id

            sdf_arg = ensure_fleet_tb3_sdf(logs_dir, robot_id, namespace, dry_run=dry_run)
            spawn_cmd = spawn_robot_command(
                robot_id, namespace, x, y, sdf_arg
            )
            bridge_cmd = bridge_command(robot_id, world["world_id"], namespace, backend_url)
            rsp_cmd = robot_state_publisher_launch_command(namespace)
            use_fleet_tf = sdf_arg is not None

            if dry_run:
                print(f"[DRY-RUN] {spawn_cmd}")
                if use_fleet_tf:
                    print(f"[DRY-RUN] {rsp_cmd}")
                print(f"[DRY-RUN] {bridge_cmd}")
                launched = True
            else:
                print(f"[fleet] Spawning {robot_id} in {world['world_id']} at ({x:.1f}, {y:.1f}) ...")
                spawn_log = logs_dir / f"spawn_{robot_id}.log"
                rsp_log = logs_dir / f"rsp_{robot_id}.log"
                bridge_log = logs_dir / f"bridge_{robot_id}.log"
                spawn_ok = run_blocking(spawn_cmd, spawn_log)
                rsp_ok = True
                if spawn_ok and use_fleet_tf:
                    print(f"[fleet] {robot_id} — starting robot_state_publisher ...")
                    rsp_ok = run_detached(rsp_cmd, rsp_log)
                bridge_ok = False
                if spawn_ok and rsp_ok:
                    print(f"[fleet] {robot_id} — starting bridge ...")
                    bridge_ok = run_detached(bridge_cmd, bridge_log)
                launched = spawn_ok and rsp_ok and bridge_ok
                if launched:
                    print(f"[fleet] {robot_id} ready")

            if not launched:
                raise RuntimeError(
                    f"Failed to launch robot resources for {robot_id}. "
                    f"Check logs in {logs_dir}"
                )

            world["robots"].append(robot_id)
            existing_robot_ids.add(robot_id)
            state["next_robot_index"] += 1
            pending -= 1
            free_slots -= 1

    while pending > 0:
        world_id = make_world_id(state["next_world_index"])
        world_name = f"sim_world_{state['next_world_index']:02d}"

        world_cmd = world_launch_command(headless, world_name)
        if dry_run:
            print(f"[DRY-RUN] {world_cmd}")
            world_started = True
        elif skip_world_launch:
            print(
                f"[fleet] --skip-world-launch: not starting Gazebo; "
                f"waiting for /spawn_entity ({world_id}) ..."
            )
            time.sleep(3.0)
            world_started = wait_for_service("/spawn_entity", timeout_sec=90)
            if not world_started:
                raise RuntimeError(
                    f"/spawn_entity not available for {world_id}. "
                    f"Start gzserver first or drop --skip-world-launch."
                )
            print("[fleet] Gazebo spawn service ready.")
        else:
            print(f"[fleet] Starting Gazebo world {world_id} ({'headless' if headless else 'GUI'}) ...")
            world_log = logs_dir / f"world_{world_id}.log"
            world_started = run_detached(world_cmd, world_log)

            if not world_started:
                raise RuntimeError(
                    f"Failed to start world for {world_id}. "
                    f"Check logs in {logs_dir}"
                )

            print(f"[fleet] Waiting for Gazebo to be ready (up to 24s) ...")
            time.sleep(4.0)
            if not wait_for_service("/spawn_entity", timeout_sec=20):
                raise RuntimeError(
                    f"World started but /spawn_entity service did not become ready for {world_id}. "
                    f"Check logs in {logs_dir}"
                )
            print(f"[fleet] Gazebo ready.")

        world = {
            "world_id": world_id,
            "world_name": world_name,
            "capacity": robots_per_world,
            "headless": headless,
            "robots": [],
        }
        worlds.append(world)
        state["next_world_index"] += 1

        free_slots = robots_per_world
        while pending > 0 and free_slots > 0:
            robot_id = make_robot_id(state["next_robot_index"])
            while robot_id in existing_robot_ids:
                state["next_robot_index"] += 1
                robot_id = make_robot_id(state["next_robot_index"])

            slot_index = len(world["robots"])
            x = (slot_index % 5) * 1.0
            y = (slot_index // 5) * 1.0
            namespace = robot_id

            sdf_arg = ensure_fleet_tb3_sdf(logs_dir, robot_id, namespace, dry_run=dry_run)
            spawn_cmd = spawn_robot_command(
                robot_id, namespace, x, y, sdf_arg
            )
            bridge_cmd = bridge_command(robot_id, world_id, namespace, backend_url)
            rsp_cmd = robot_state_publisher_launch_command(namespace)
            use_fleet_tf = sdf_arg is not None

            if dry_run:
                print(f"[DRY-RUN] {spawn_cmd}")
                if use_fleet_tf:
                    print(f"[DRY-RUN] {rsp_cmd}")
                print(f"[DRY-RUN] {bridge_cmd}")
                launched = True
            else:
                print(f"[fleet] Spawning {robot_id} in {world_id} at ({x:.1f}, {y:.1f}) ...")
                spawn_log = logs_dir / f"spawn_{robot_id}.log"
                rsp_log = logs_dir / f"rsp_{robot_id}.log"
                bridge_log = logs_dir / f"bridge_{robot_id}.log"
                spawn_ok = run_blocking(spawn_cmd, spawn_log)
                rsp_ok = True
                if spawn_ok and use_fleet_tf:
                    print(f"[fleet] {robot_id} — starting robot_state_publisher ...")
                    rsp_ok = run_detached(rsp_cmd, rsp_log)
                bridge_ok = False
                if spawn_ok and rsp_ok:
                    print(f"[fleet] {robot_id} — starting bridge ...")
                    bridge_ok = run_detached(bridge_cmd, bridge_log)
                launched = spawn_ok and rsp_ok and bridge_ok
                if launched:
                    print(f"[fleet] {robot_id} ready")

            if not launched:
                raise RuntimeError(
                    f"Failed to launch robot resources for {robot_id}. "
                    f"Check logs in {logs_dir}"
                )

            world["robots"].append(robot_id)
            existing_robot_ids.add(robot_id)
            state["next_robot_index"] += 1
            pending -= 1
            free_slots -= 1


def main():
    args = parse_args()

    if args.count <= 0:
        raise ValueError("--count must be > 0")
    if args.robots_per_world <= 0:
        raise ValueError("--robots-per-world must be > 0")

    state_path = Path(args.state_file).expanduser().resolve()
    state = load_state(state_path)
    working_state = copy.deepcopy(state) if args.dry_run else state
    logs_dir = state_path.parent / ".fleet_logs"

    allocate_robots(
        count=args.count,
        state=working_state,
        robots_per_world=args.robots_per_world,
        headless=args.headless,
        dry_run=args.dry_run,
        backend_url=args.backend_url.rstrip("/"),
        logs_dir=logs_dir,
        skip_world_launch=args.skip_world_launch,
    )

    if not args.dry_run:
        save_state(state_path, working_state)

    print(f"State file: {state_path}")
    for world in working_state["worlds"]:
        print(
            f"{world['world_id']} ({world['world_name']}): "
            f"{len(world['robots'])}/{world['capacity']} robots"
        )


if __name__ == "__main__":
    main()
