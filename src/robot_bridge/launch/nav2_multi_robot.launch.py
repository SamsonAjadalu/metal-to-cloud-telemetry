"""Per-robot Nav2 bringup for namespaced TurtleBot3 sim (bringup_launch + tf relay + param patches)."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    OpaqueFunction,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from nav2_common.launch import ReplaceString

ROBOT_NAMESPACES = ['tb3_001', 'tb3_002', 'tb3_003']


def launch_setup(context, *args, **kwargs):
    bringup_dir = get_package_share_directory('nav2_bringup')
    tb3_nav_share = get_package_share_directory('turtlebot3_navigation2')
    burger_params = os.path.join(tb3_nav_share, 'param', 'humble', 'burger.yaml')

    map_path = LaunchConfiguration('map').perform(context)
    use_rviz = LaunchConfiguration('use_rviz').perform(context).lower() in (
        'true',
        '1',
        'yes',
    )

    use_comp = LaunchConfiguration('use_composition').perform(context)

    actions = []
    for i, ns in enumerate(ROBOT_NAMESPACES):
        actions.append(
            Node(
                package='robot_bridge',
                executable='tf_global_relay',
                namespace=ns,
                name=f'tf_relay_{ns}',
                parameters=[{'use_sim_time': True}],
                output='screen',
            )
        )
        params_namespaced = ReplaceString(
            source_file=burger_params,
            replacements={
                'recoveries_server:': 'behavior_server:',
                'recovery_plugins:': 'behavior_plugins:',
                'nav2_recoveries/': 'nav2_behaviors/',
                'odom_topic: /odom': 'odom_topic: odom',
                'topic: /scan': 'topic: scan',
                'base_frame_id: "base_footprint"': (
                    f'base_frame_id: "{ns}/base_footprint"'
                ),
                'odom_frame_id: "odom"': f'odom_frame_id: "{ns}/odom"',
                'robot_base_frame: base_link': f'robot_base_frame: {ns}/base_link',
                'global_frame: odom': f'global_frame: {ns}/odom',
                'local_frame: odom': f'local_frame: {ns}/odom',
                'transform_tolerance: 1.0': 'transform_tolerance: 3.0',
            },
        )
        actions.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(bringup_dir, 'launch', 'bringup_launch.py')
                ),
                launch_arguments={
                    'namespace': ns,
                    'use_namespace': 'true',
                    'map': map_path,
                    'use_sim_time': 'true',
                    'use_composition': use_comp,
                    'params_file': params_namespaced,
                }.items(),
            )
        )
        if use_rviz and i == 0:
            rviz_cfg = ReplaceString(
                source_file=os.path.join(
                    bringup_dir, 'rviz', 'nav2_namespaced_view.rviz'
                ),
                replacements={'<robot_namespace>': f'/{ns}'},
            )
            actions.append(
                Node(
                    package='rviz2',
                    executable='rviz2',
                    namespace=ns,
                    name='rviz2',
                    arguments=['-d', rviz_cfg],
                    parameters=[{'use_sim_time': True}],
                    output='screen',
                    remappings=[
                        ('/map', 'map'),
                        ('/tf', 'tf'),
                        ('/tf_static', 'tf_static'),
                        ('/goal_pose', 'goal_pose'),
                        ('/clicked_point', 'clicked_point'),
                        ('/initialpose', 'initialpose'),
                    ],
                )
            )

    seed = LaunchConfiguration('seed_amcl').perform(context).lower() in (
        'true',
        '1',
        'yes',
    )
    if seed:
        delay = float(LaunchConfiguration('seed_delay').perform(context))
        actions.append(
            TimerAction(
                period=delay,
                actions=[
                    ExecuteProcess(
                        cmd=[
                            'ros2',
                            'run',
                            'robot_bridge',
                            'amcl_seed_pose',
                            *ROBOT_NAMESPACES,
                        ],
                        output='screen',
                    )
                ],
            )
        )
    return actions


def generate_launch_description():
    default_map = os.path.join(
        get_package_share_directory('turtlebot3_navigation2'), 'map', 'map.yaml'
    )

    return LaunchDescription(
        [
            SetEnvironmentVariable('TURTLEBOT3_MODEL', 'burger'),
            DeclareLaunchArgument(
                'map',
                default_value=default_map,
                description='Path to map yaml (shared by all robots).',
            ),
            DeclareLaunchArgument(
                'use_rviz',
                default_value='true',
                description='If true, start one RViz for the first namespace only.',
            ),
            DeclareLaunchArgument(
                'use_composition',
                default_value='False',
                description='Nav2 composition per robot (True/False per bringup).',
            ),
            DeclareLaunchArgument(
                'seed_amcl',
                default_value='true',
                description='Run amcl_seed_pose after seed_delay.',
            ),
            DeclareLaunchArgument(
                'seed_delay',
                default_value='28.0',
                description='Seconds after this launch before amcl_seed_pose.',
            ),
            OpaqueFunction(function=launch_setup),
        ]
    )
