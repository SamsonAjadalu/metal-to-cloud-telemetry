def generate_launch_description():

from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable, TimerAction
from launch_ros.actions import ComposableNodeContainer, ComposableNode

# List your robot namespaces here
robot_namespaces = ["tb3_001", "tb3_002", "tb3_003"]

map_path = "/opt/ros/humble/share/turtlebot3_navigation2/map/map.yaml"
tb3_model = "burger"  # Change if needed

actions = [
    SetEnvironmentVariable("TURTLEBOT3_MODEL", tb3_model)
]

for ns in robot_namespaces:
    env = {"TURTLEBOT3_MODEL": tb3_model}
    # Launch map_server
    actions.append(
        ExecuteProcess(
            cmd=[
                "ros2", "run", "nav2_map_server", "map_server",
                "--ros-args", f"-r __ns:={ns}", f"-p yaml_filename:={map_path}"
            ],
            output="screen",
            additional_env=env
        )
    )
    # Configure map_server lifecycle
    actions.append(
        TimerAction(
            period=3.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        "ros2", "lifecycle", "set", f"/{ns}/map_server", "configure"
                    ],
                    output="screen",
                    additional_env=env
                )
            ]
        )
    )
    # Activate map_server lifecycle
    actions.append(
        TimerAction(
            period=5.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        "ros2", "lifecycle", "set", f"/{ns}/map_server", "activate"
                    ],
                    output="screen",
                    additional_env=env
                )
            ]
        )
    )
    # Launch AMCL as a component in nav2_container
    actions.append(
        ComposableNodeContainer(
            name=f"nav2_container_{ns}",
            namespace=ns,
            package="rclcpp_components",
            executable="component_container",
            composable_node_descriptions=[
                ComposableNode(
                    package="nav2_amcl",
                    plugin="nav2_amcl::AmclNode",
                    name="amcl",
                    parameters=[{"use_sim_time": True}],
                )
            ],
            output="screen",
            additional_env=env
        )
    )
    # Launch Nav2 stack
    actions.append(
        ExecuteProcess(
            cmd=[
                "ros2", "launch", "turtlebot3_navigation2", "navigation2.launch.py",
                "use_sim_time:=true",
                f"namespace:={ns}",
                f"map:={map_path}"
            ],
            output="screen",
            additional_env=env
        )
    )
    env = {"TURTLEBOT3_MODEL": tb3_model}
    # Launch map_server
    actions.append(
        ExecuteProcess(
            cmd=[
                "ros2", "run", "nav2_map_server", "map_server",
                "--ros-args", f"-r __ns:={ns}", f"-p yaml_filename:={map_path}"
            ],
            output="screen",
            additional_env=env
        )
    )
    # Configure map_server lifecycle
    actions.append(
        TimerAction(
            period=3.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        "ros2", "lifecycle", "set", f"/{ns}/map_server", "configure"
                    ],
                    output="screen",
                    additional_env=env
                )
            ]
        )
    )
    # Activate map_server lifecycle
    actions.append(
        TimerAction(
            period=5.0,
            actions=[
                ExecuteProcess(
                    cmd=[
                        "ros2", "lifecycle", "set", f"/{ns}/map_server", "activate"
                    ],
                    output="screen",
                    additional_env=env
                )
            ]
        )
    )
    # Launch AMCL with explicit params
    actions.append(
        ExecuteProcess(
            cmd=[
                "ros2", "run", "nav2_amcl", "amcl",
                "--ros-args", f"-r __ns:={ns}",
                f"-p use_sim_time:=true"
            ],
            output="screen",
            additional_env=env
        )
    )
    # Launch Nav2 stack
    actions.append(
        ExecuteProcess(
            cmd=[
                "ros2", "launch", "turtlebot3_navigation2", "navigation2.launch.py",
                "use_sim_time:=true",
                f"namespace:={ns}",
                f"map:={map_path}"
            ],
            output="screen",
            additional_env=env
        )
    )

def generate_launch_description():
    return LaunchDescription(actions)
