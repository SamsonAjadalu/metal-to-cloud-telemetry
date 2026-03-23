#!/usr/bin/env python3
"""Relay /tf and /tf_static into this node's namespace for namespaced Nav2."""

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from tf2_msgs.msg import TFMessage


def main(args=None):
    rclpy.init(args=args)
    node = Node('tf_global_relay')

    sub_qos = QoSProfile(
        history=HistoryPolicy.KEEP_LAST,
        depth=1000,
        reliability=ReliabilityPolicy.RELIABLE,
        durability=DurabilityPolicy.VOLATILE,
    )
    static_qos = QoSProfile(
        history=HistoryPolicy.KEEP_LAST,
        depth=200,
        reliability=ReliabilityPolicy.RELIABLE,
        durability=DurabilityPolicy.TRANSIENT_LOCAL,
    )
    pub_tf = node.create_publisher(TFMessage, 'tf', sub_qos)
    pub_tf_static = node.create_publisher(TFMessage, 'tf_static', static_qos)

    def on_tf(msg: TFMessage):
        if msg.transforms:
            pub_tf.publish(msg)

    def on_tf_static(msg: TFMessage):
        if msg.transforms:
            pub_tf_static.publish(msg)

    node.create_subscription(TFMessage, '/tf', on_tf, sub_qos)
    node.create_subscription(TFMessage, '/tf_static', on_tf_static, static_qos)

    node.get_logger().info(
        'Relaying /tf and /tf_static into this namespace for Nav2 compatibility.'
    )
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
