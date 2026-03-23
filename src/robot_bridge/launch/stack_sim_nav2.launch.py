"""Gazebo (gzserver) + timed fleet spawn + Nav2. Uses /tmp fleet state so indices stay aligned with nav2_multi_robot."""

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
            '--backend-url',
            LaunchConfiguration('backend_url'),
        ],
        output='screen',
    )

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_launch),
        launch_arguments={
            'use_rviz': LaunchConfiguration('use_rviz'),
            'seed_delay': LaunchConfiguration('seed_delay'),
        }.items(),
    )

    return LaunchDescription(
        [
            SetEnvironmentVariable('TURTLEBOT3_MODEL', 'burger'),
            SetEnvironmentVariable('USE_SIM_TIME', 'true'),
            SetEnvironmentVariable('FASTDDS_BUILTIN_TRANSPORTS', 'UDPv4'),
            DeclareLaunchArgument(
                'count',
                default_value='3',
                description='Robot count; must match nav2_multi_robot.',
            ),
            DeclareLaunchArgument(
                'backend_url',
                default_value='ws://159.203.4.11:8000',
                description='Telemetry backend base URL (no /ws path).',
            ),
            DeclareLaunchArgument(
                'headless',
                default_value='false',
                description='Headless: no Gazebo GUI.',
            ),
            DeclareLaunchArgument(
                'use_rviz',
                default_value='true',
                description='Start RViz (first robot only).',
            ),
            DeclareLaunchArgument(
                'fleet_delay',
                default_value='12.0',
                description='Delay before fleet_orchestrator (s).',
            ),
            DeclareLaunchArgument(
                'nav2_delay',
                default_value='35.0',
                description='Delay before Nav2 launch (s).',
            ),
            DeclareLaunchArgument(
                'seed_delay',
                default_value='18.0',
                description='Delay after Nav2 starts before amcl_seed_pose (s).',
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
