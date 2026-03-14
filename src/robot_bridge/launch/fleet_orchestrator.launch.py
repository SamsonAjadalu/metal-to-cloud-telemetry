from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    count_arg = DeclareLaunchArgument("count", default_value="1")

    run_orchestrator = ExecuteProcess(
        cmd=[
            "ros2",
            "run",
            "robot_bridge",
            "fleet_orchestrator",
            "--count",
            LaunchConfiguration("count"),
        ],
        output="screen",
    )

    return LaunchDescription([count_arg, run_orchestrator])
