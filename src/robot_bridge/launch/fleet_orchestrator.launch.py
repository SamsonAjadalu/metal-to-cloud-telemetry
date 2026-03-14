from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    count_arg = DeclareLaunchArgument("count", default_value="1")
    robots_per_world_arg = DeclareLaunchArgument("robots_per_world", default_value="20")
    headless_arg = DeclareLaunchArgument("headless", default_value="false")
    state_file_arg = DeclareLaunchArgument("state_file", default_value="fleet_state.json")
    backend_url_arg = DeclareLaunchArgument("backend_url", default_value="ws://localhost:8000")
    dry_run_arg = DeclareLaunchArgument("dry_run", default_value="false")

    run_orchestrator = ExecuteProcess(
        cmd=[
            "ros2",
            "run",
            "robot_bridge",
            "fleet_orchestrator",
            "--count",
            LaunchConfiguration("count"),
            "--robots-per-world",
            LaunchConfiguration("robots_per_world"),
            "--headless",
            LaunchConfiguration("headless"),
            "--state-file",
            LaunchConfiguration("state_file"),
            "--backend-url",
            LaunchConfiguration("backend_url"),
            "--dry-run",
            LaunchConfiguration("dry_run"),
        ],
        output="screen",
    )

    return LaunchDescription(
        [
            count_arg,
            robots_per_world_arg,
            headless_arg,
            state_file_arg,
            backend_url_arg,
            dry_run_arg,
            run_orchestrator,
        ]
    )
