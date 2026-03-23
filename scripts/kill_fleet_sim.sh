#!/usr/bin/env bash
# Tear down stack_sim / Gazebo / Nav2 / bridges before a clean restart.
set -euo pipefail

pkill -f "ros2 launch robot_bridge stack_sim_nav2" 2>/dev/null || true
pkill -f "ros2 launch robot_bridge" 2>/dev/null || true
pkill -f "robot_bridge.fleet_orchestrator" 2>/dev/null || true
pkill -f "ros2 run robot_bridge telemetry_bridge" 2>/dev/null || true
pkill -f "telemetry_bridge" 2>/dev/null || true
pkill -f spawn_entity.py 2>/dev/null || true
pkill -f gzserver 2>/dev/null || true
pkill -f gzclient 2>/dev/null || true
pkill -f rviz2 2>/dev/null || true
pkill -f robot_state_publisher 2>/dev/null || true

sleep 0.5
pkill -9 -f gzserver 2>/dev/null || true
pkill -9 -f gzclient 2>/dev/null || true

echo "Kill pass done. Check: ros2 node list (should be empty or only unrelated nodes)."
