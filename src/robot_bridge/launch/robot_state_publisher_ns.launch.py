"""One TurtleBot3 robot_state_publisher under a ROS namespace (matches namespaced TF frames)."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description():
    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')

    model = os.environ.get('TURTLEBOT3_MODEL', 'burger')
    urdf_path = os.path.join(
        get_package_share_directory('turtlebot3_gazebo'),
        'urdf',
        f'turtlebot3_{model}.urdf',
    )
    with open(urdf_path, 'r', encoding='utf-8') as infp:
        robot_desc = infp.read()

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'namespace',
                description='Robot id / namespace, e.g. tb3_001 (no leading slash)',
            ),
            DeclareLaunchArgument(
                'use_sim_time',
                default_value='true',
                description='Must match Gazebo clock',
            ),
            GroupAction(
                [
                    PushRosNamespace(namespace),
                    Node(
                        package='robot_state_publisher',
                        executable='robot_state_publisher',
                        name='robot_state_publisher',
                        output='screen',
                        parameters=[
                            {
                                'use_sim_time': use_sim_time,
                                'robot_description': robot_desc,
                                'frame_prefix': PythonExpression(
                                    ["'", namespace, "/'"]
                                ),
                            }
                        ],
                    ),
                ]
            ),
        ]
    )
