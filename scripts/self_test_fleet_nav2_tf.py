#!/usr/bin/env python3
"""
Offline checks for multi-robot sim TF + Nav2 alignment (tb3_XXX/odom on /tf → namespaced /tf).

Run (from anywhere, with ROS 2 Humble sourced):
  source /opt/ros/humble/setup.bash
  source /path/to/workspace/install/setup.bash
  python3 scripts/self_test_fleet_nav2_tf.py

Optional live checks (no Gazebo required; needs a running graph):
  python3 scripts/self_test_fleet_nav2_tf.py --live
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_namespaced_sdf() -> list[str]:
    errors: list[str] = []
    try:
        sys.path.insert(0, str(_repo_root() / "src" / "robot_bridge"))
        from robot_bridge.fleet_orchestrator import write_namespaced_tb3_sdf
    except ImportError as e:
        return [f"fleet_orchestrator import failed (source workspace?): {e}"]

    ns = "tb3_001"
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "probe.sdf"
        try:
            write_namespaced_tb3_sdf(ns, "burger", p)
        except Exception as e:
            return [f"write_namespaced_tb3_sdf: {e}"]
        text = p.read_text(encoding="utf-8")
        om = re.search(r"<odometry_frame>([^<]+)</odometry_frame>", text)
        bm = re.search(r"<robot_base_frame>([^<]+)</robot_base_frame>", text)
        if not om:
            errors.append("no <odometry_frame> in generated SDF")
        elif om.group(1).strip() != f"{ns}/odom":
            errors.append(f"odometry_frame want {ns}/odom, got {om.group(1)!r}")
        if not bm:
            errors.append("no <robot_base_frame> in generated SDF")
        elif bm.group(1).strip() != f"{ns}/base_footprint":
            errors.append(f"robot_base_frame want {ns}/base_footprint, got {bm.group(1)!r}")
    return errors


def test_burger_nav2_params() -> list[str]:
    errors: list[str] = []
    try:
        import yaml
        from ament_index_python.packages import get_package_share_directory
        from launch import LaunchContext
        from nav2_common.launch import ReplaceString
    except ImportError as e:
        return [f"ROS Python deps missing: {e}"]

    ns = "tb3_001"
    burger = os.path.join(
        get_package_share_directory("turtlebot3_navigation2"),
        "param",
        "humble",
        "burger.yaml",
    )
    params = ReplaceString(
        source_file=burger,
        replacements={
            "recoveries_server:": "behavior_server:",
            "recovery_plugins:": "behavior_plugins:",
            "nav2_recoveries/": "nav2_behaviors/",
            "odom_topic: /odom": "odom_topic: odom",
            "topic: /scan": "topic: scan",
            'base_frame_id: "base_footprint"': f'base_frame_id: "{ns}/base_footprint"',
            'odom_frame_id: "odom"': f'odom_frame_id: "{ns}/odom"',
            "robot_base_frame: base_link": f"robot_base_frame: {ns}/base_link",
            "global_frame: odom": f"global_frame: {ns}/odom",
            "local_frame: odom": f"local_frame: {ns}/odom",
        },
    )
    path = params.perform(LaunchContext())
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    want = f"{ns}/odom"
    frames: set[str] = set()

    def walk(obj):
        if isinstance(obj, dict):
            gf = obj.get("global_frame")
            if isinstance(gf, str):
                frames.add(gf)
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    walk(data)
    if want not in frames:
        errors.append(
            f"no global_frame {want!r} in rewritten yaml (seen: {sorted(frames)!r})"
        )
    return errors


def live_ros2_checks() -> list[str]:
    errors: list[str] = []
    ros2 = shutil_which("ros2")
    if not ros2:
        return ["ros2 CLI not found in PATH"]

    def run(args: list[str], timeout: float = 8.0) -> tuple[int, str]:
        try:
            p = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=os.environ.copy(),
            )
            return p.returncode, (p.stdout or "") + (p.stderr or "")
        except subprocess.TimeoutExpired:
            return -1, "timeout"
        except FileNotFoundError:
            return -1, "not found"

    code, out = run([ros2, "topic", "list"])
    if code != 0:
        errors.append(f"ros2 topic list failed: {out[:500]}")
        return errors

    if "/tf" not in out.splitlines():
        errors.append("no /tf topic (is Gazebo or a TF publisher running?)")
        return errors

    # One message; user may see nothing if sim paused or no publishers
    code, sample = run(
        [ros2, "topic", "echo", "/tf", "--once"],
        timeout=15.0,
    )
    if code != 0 or "transforms:" not in sample:
        errors.append(
            "ros2 topic echo /tf --once: no sample (publishers off or QoS mismatch)."
        )
        return errors

    if "tb3_001/odom" not in sample and "tb3_002/odom" not in sample:
        errors.append(
            "sample /tf has no tb3_XXX/odom frames — check fleet SDF spawn or diff_drive."
        )

    code, info = run([ros2, "topic", "info", "/tf", "-v"], timeout=8.0)
    if code == 0 and info:
        print("--- /tf endpoint summary ---\n", info[:2500])
    return errors


def shutil_which(cmd: str) -> str | None:
    from shutil import which

    return which(cmd)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--live",
        action="store_true",
        help="Run ros2 topic checks against a live ROS graph",
    )
    args = ap.parse_args()

    errs: list[str] = []
    errs.extend(test_namespaced_sdf())
    errs.extend(test_burger_nav2_params())

    print("Offline checks:")
    if errs:
        for e in errs:
            print("  FAIL:", e)
        return 1
    print("  OK: namespaced TurtleBot3 SDF (odometry_frame / robot_base_frame)")
    print("  OK: ReplaceString burger.yaml → local_costmap global_frame tb3_001/odom")

    if args.live:
        print("\nLive checks:")
        live_errs = live_ros2_checks()
        if live_errs:
            for e in live_errs:
                print("  FAIL:", e)
            return 1
        print("  OK: /tf sample includes namespaced odom (or topic reachable)")

    print("\nIf Nav2 still logs 'Invalid frame ID \"tb3_XXX/odom\"':")
    print("  - Ensure tf_global_relay nodes run (one per namespace).")
    print("  - ros2 topic hz /tf  and  ros2 topic hz /tb3_001/tf")
    print("  - stack_sim_nav2.launch.py sets FASTDDS_BUILTIN_TRANSPORTS=UDPv4 to limit SHM issues.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
