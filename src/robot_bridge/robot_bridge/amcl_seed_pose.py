"""Publish initialpose per namespace for AMCL (sim)."""

from __future__ import annotations

import sys
import time

import rclpy
import tf2_ros
from rclpy.duration import Duration
from rclpy.parameter import Parameter
from geometry_msgs.msg import PoseWithCovarianceStamped
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from rclpy.time import Time
from rclpy.utilities import remove_ros_args

from robot_bridge.spawn_layout import spawn_xy_for_slot


def main() -> None:
    argv = remove_ros_args(sys.argv)
    if len(argv) > 1:
        namespaces = argv[1:]
    else:
        namespaces = ['tb3_001', 'tb3_002', 'tb3_003']

    rclpy.init()
    node = Node(
        'amcl_seed_pose',
        parameter_overrides=[Parameter('use_sim_time', value=True)],
    )

    # Volatile QoS to match AMCL's initialpose sub.
    qos = QoSProfile(
        depth=10,
        reliability=ReliabilityPolicy.RELIABLE,
        durability=DurabilityPolicy.VOLATILE,
    )

    pubs = []
    for ns in namespaces:
        pubs.append(
            (
                ns,
                node.create_publisher(
                    PoseWithCovarianceStamped, f'/{ns}/initialpose', qos
                ),
            )
        )

    for _ in range(20):
        rclpy.spin_once(node, timeout_sec=0.05)

    # Wait for odom→base_scan in /tf so AMCL does not reject scans.
    tf_buf = tf2_ros.Buffer(cache_time=Duration(seconds=30.0))
    _ = tf2_ros.TransformListener(tf_buf, node)
    deadline = time.monotonic() + 90.0
    pending = list(namespaces)
    while pending and time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)
        still = []
        for ns in pending:
            try:
                tf_buf.lookup_transform(f'{ns}/odom', f'{ns}/base_scan', Time())
            except tf2_ros.TransformException:
                still.append(ns)
                continue
        pending = still
    if pending:
        node.get_logger().warn(
            f'TF not ready for {pending} (odom→base_scan); seeding anyway.'
        )

    for i, (ns, pub) in enumerate(pubs):
        msg = PoseWithCovarianceStamped()
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        x, y = spawn_xy_for_slot(i)
        msg.pose.pose.position.x = x
        msg.pose.pose.position.y = y
        msg.pose.pose.position.z = 0.0
        msg.pose.pose.orientation.w = 1.0
        c = msg.pose.covariance
        c[0] = 0.25
        c[7] = 0.25
        c[35] = 0.06853891909122467
        pub.publish(msg)
        node.get_logger().info(f'seeded AMCL initial pose for {ns} at map ({x:.2f}, {y:.2f})')
        time.sleep(0.15)

    time.sleep(0.2)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
