"""
Multi-robot Nav2 for namespaced TurtleBot3 sims (e.g. tb3_001, tb3_002).

Important: turtlebot3_navigation2/navigation2.launch.py does NOT forward namespace to
nav2_bringup, so passing namespace:=... to that launch is a no-op and stacks collide
on /map, /tf, etc. This file includes bringup_launch.py correctly per robot.

Prerequisites: Robots spawned with **per-robot TF frame prefixes** matching `{ns}/odom`,
`{ns}/base_footprint`, `{ns}/base_link` (fleet_orchestrator default spawn does this), plus
`/{ns}/odom`, `/{ns}/scan` topics.

Gazebo diff_drive publishes `{ns}/odom`→`{ns}/base_footprint`; robot_state_publisher adds
`{ns}/base_link`. Nav2 params below are rewritten to use those frame ids.

This launch does **not** replace Gazebo odometry TF.
The **map** TF edge **map→odom** is published by **AMCL** after localization. By default,
**seed_amcl** runs **amcl_seed_pose** after **seed_delay** seconds (poses match fleet grid).
Set **seed_amcl:=false** to localize manually (**2D Pose Estimate** in RViz).

**RViz + Gazebo:** RViz must use **use_sim_time=true** or it ignores sim-timed TF and you see
"No tf data" / "Frame [map] does not exist" even when topics look fine.

**TF relay:** Gazebo publishes on absolute `/tf` (`TransformBroadcaster` uses hardcoded `/tf`).
Bringup remaps `/tf`→`tf`, and `tf2_ros::TransformListener` still honors that remap, so each Nav2
stack only subscribes to `/{ns}/tf` — not the global topic. `tf_global_relay` copies global
`/tf` and `/tf_static` into each namespace so those listeners see `tb3_XXX/odom` etc.

**Composition:** By default **use_composition:=false** so each Nav2 node runs in its own process.
A single `component_container_isolated` shared by the full stack can starve AMCL laser callbacks
(message filter queue full, no `map`→`odom`). Set **use_composition:=true** if you need lower RAM
and accept that risk (e.g. fewer robots).

**TurtleBot3 burger.yaml:** still declares `recoveries_server` / `recovery_plugins` / `nav2_recoveries/*`.
Nav2 humble uses the `behavior_server` node name and `behavior_plugins`; we rewrite those so
`global_frame` / `robot_base_frame` namespacing actually applies (fixes missing frame `odom`).
"""

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

# Must match simulation + telemetry_bridge topics (e.g. /tb3_001/cmd_vel).
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
        # Gazebo publishes on /tf; Nav2 (remapped /tf->tf) listens on /{ns}/tf only.
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
        # Match fleet SDF patch: TF frames are tb3_XXX/odom on the global /tf graph.
        # turtlebot3 burger.yaml still names this block recoveries_server and uses
        # recovery_plugins / nav2_recoveries/*; Nav2 humble's composable node is
        # behavior_server and ignores that block — then TF defaults to frame "odom",
        # which does not exist when sim uses tb3_XXX/odom.
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
                # AMCL message filter: stale scans vs 10s TF cache when sim is loaded / CPU-heavy.
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
        # One namespaced RViz. nav2_bringup/rviz_launch.py omits use_sim_time on the
        # namespaced Node — with Gazebo, RViz then drops all TF → "No tf data".
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
                description=(
                    'If True, one composed Nav2 container per robot (lighter RAM); '
                    'False recommended for multi-robot sim so AMCL keeps up with /scan. '
                    'Must be True/False (capitalized) — matches nav2_bringup PythonExpression.'
                ),
            ),
            DeclareLaunchArgument(
                'seed_amcl',
                default_value='true',
                description='If true, publish initialpose for each robot after seed_delay (sim).',
            ),
            DeclareLaunchArgument(
                'seed_delay',
                default_value='28.0',
                description=(
                    'Seconds after **this** launch starts (parent stack: after Nav2 is started) '
                    'before amcl_seed_pose runs.'
                ),
            ),
            OpaqueFunction(function=launch_setup),
        ]
    )
