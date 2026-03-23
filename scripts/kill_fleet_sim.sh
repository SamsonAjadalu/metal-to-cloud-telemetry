#!/usr/bin/env bash
# Tear down stack_sim / Gazebo / Nav2 / bridges before a clean restart.
set -euo pipefail

pkill -9 -f "ros2 launch robot_bridge stack_sim_nav2.launch.py" 2>/dev/null || true
pkill -9 -f "ros2 launch robot_bridge stack_sim_nav2" 2>/dev/null || true
pkill -9 -f "ros2 launch robot_bridge" 2>/dev/null || true

pkill -9 -f "robot_bridge.fleet_orchestrator" 2>/dev/null || true
pkill -9 -f "ros2 run robot_bridge telemetry_bridge" 2>/dev/null || true
pkill -9 -f "telemetry_bridge" 2>/dev/null || true
pkill -9 -f "robot_bridge.amcl_seed_pose" 2>/dev/null || true
pkill -9 -f "amcl_seed_pose" 2>/dev/null || true

# Nav2 uses nav2_lifecycle_manager/lifecycle_manager; ensure it is killed per-namespace.
pkill -9 -f "nav2_lifecycle_manager/lifecycle_manager" 2>/dev/null || true
pkill -9 -f "lifecycle_manager_navigation" 2>/dev/null || true
pkill -9 -f "lifecycle_manager_localization" 2>/dev/null || true
pkill -f spawn_entity.py 2>/dev/null || true
pkill -f gzserver 2>/dev/null || true
pkill -f gzclient 2>/dev/null || true
pkill -f rviz2 2>/dev/null || true
pkill -f robot_state_publisher 2>/dev/null || true

sleep 0.5
pkill -9 -f gzserver 2>/dev/null || true
pkill -9 -f gzclient 2>/dev/null || true

sleep 2
echo "Kill pass done. Current ros2 nodes (may include unrelated):"
ros2 node list 2>/dev/null || true
