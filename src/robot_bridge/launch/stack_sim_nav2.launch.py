"""
One terminal: Gazebo (gzserver only, no extra default TurtleBot spawn) → fleet → Nav2.

Why not `turtlebot3_world.launch.py` + fleet?
  That launch already spawns a default TurtleBot and starts its own stack; fleet would
  start a *second* Gazebo if it needs a new world. Use this file OR manual fleet+world,
  not both.

Order:
  1) gzserver with turtlebot3_world.world
  2) After `fleet_delay`, fleet_orchestrator with --skip-world-launch (spawn tb3_001…)
  3) After `nav2_delay`, nav2_multi_robot.launch.py (must match ROBOT_NAMESPACES / count)

Tune delays if your machine is slow. Match `count` to `ROBOT_NAMESPACES` in
nav2_multi_robot.launch.py (default 3).

Fleet state: this launch writes a **fresh ephemeral** state file under /tmp so the next
robots are always tb3_001, tb3_002, … matching Nav2. Your workspace `fleet_state.json` is
**not** used here — otherwise a long-lived file with next_robot_index=13 would spawn
tb3_013+ while Nav2 still expects tb3_001/odom (broken TF).
"""

import json
import os
import tempfile
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.conditions import UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import EqualsSubstitution, LaunchConfiguration


def generate_launch_description():
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    pkg_tb3 = get_package_share_directory('turtlebot3_gazebo')
    pkg_rb = get_package_share_directory('robot_bridge')

    # Ephemeral fleet state: empty map_01 so orchestrator spawns from tb3_001 again.
    sim_fleet_state = Path(tempfile.gettempdir()) / 'robot_bridge_stack_sim_fleet.json'
    sim_fleet_state.write_text(
        json.dumps(
            {
                'next_world_index': 2,
                'next_robot_index': 1,
                'worlds': [
                    {
                        'world_id': 'map_01',
                        'world_name': 'sim_world_01',
                        'capacity': 20,
                        'headless': False,
                        'robots': [],
                    }
                ],
            },
            indent=2,
        )
        + '\n',
        encoding='utf-8',
    )

    world_path = os.path.join(pkg_tb3, 'worlds', 'turtlebot3_world.world')
    nav2_launch = os.path.join(pkg_rb, 'launch', 'nav2_multi_robot.launch.py')

    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')
        ),
        launch_arguments={'world': world_path}.items(),
    )

    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py')
        ),
        condition=UnlessCondition(
            EqualsSubstitution(LaunchConfiguration('headless'), 'true')
        ),
    )

    fleet_proc = ExecuteProcess(
        cmd=[
            'ros2',
            'run',
            'robot_bridge',
            'fleet_orchestrator',
            '--count',
            LaunchConfiguration('count'),
            '--skip-world-launch',
            '--state-file',
            str(sim_fleet_state),
        ],
        output='screen',
    )

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_launch),
        launch_arguments={
            'use_rviz': LaunchConfiguration('use_rviz'),
            # nav2_multi_robot Timer fires from launch start; must run after Nav2 is up (nav2_delay + bringup).
            'seed_delay': LaunchConfiguration('seed_delay'),
        }.items(),
    )

    return LaunchDescription(
        [
            SetEnvironmentVariable('TURTLEBOT3_MODEL', 'burger'),
            # fleet-spawned telemetry_bridge reads this for goal_pose / odom timestamps in sim
            SetEnvironmentVariable('USE_SIM_TIME', 'true'),
            # Avoid Fast DDS SHM lock failures when many processes share the host (Gazebo + Nav2).
            SetEnvironmentVariable('FASTDDS_BUILTIN_TRANSPORTS', 'UDPv4'),
            DeclareLaunchArgument(
                'count',
                default_value='3',
                description='Robots to spawn (must match nav2_multi_robot ROBOT_NAMESPACES).',
            ),
            DeclareLaunchArgument(
                'headless',
                default_value='false',
                description="If true, no gzclient (GUI).",
            ),
            DeclareLaunchArgument(
                'use_rviz',
                default_value='true',
                description='Passed to nav2_multi_robot.launch.py',
            ),
            DeclareLaunchArgument(
                'fleet_delay',
                default_value='12.0',
                description='Seconds after gzserver before fleet_orchestrator runs.',
            ),
            DeclareLaunchArgument(
                'nav2_delay',
                default_value='35.0',
                description='Seconds after gzserver before Nav2 + RViz launch.',
            ),
            DeclareLaunchArgument(
                'seed_delay',
                default_value='18.0',
                description=(
                    'Seconds after **Nav2** starts (nav2_delay) before amcl_seed_pose. '
                    'Timer is relative to nav2 launch, not gzserver.'
                ),
            ),
            gzserver,
            gzclient,
            TimerAction(
                period=LaunchConfiguration('fleet_delay'),
                actions=[fleet_proc],
            ),
            TimerAction(
                period=LaunchConfiguration('nav2_delay'),
                actions=[nav2],
            ),
        ]
    )
