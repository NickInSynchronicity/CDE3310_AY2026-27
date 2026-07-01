#!/usr/bin/env python3
"""
tf_relay.py

Relays /tf to /{ns}/tf with a large queue to avoid message drops under load.

topic_tools relay uses a small internal queue. Under WiFi load, bursts of
TF messages (e.g. slam_toolbox's map→odom at 50 Hz) overflow the queue
and are silently dropped, causing nav2 to report "tb3_2/map does not exist"
and leaving the global_costmap stuck in "Checking transform" indefinitely.

This relay uses depth=500 so bursts are absorbed without loss.

Usage: python3 tf_relay.py <target_topic>
  e.g. python3 tf_relay.py /tb3_2/tf
"""

import sys
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy
from tf2_msgs.msg import TFMessage


class TFRelay(Node):
    def __init__(self, target_topic):
        super().__init__('tf_relay')

        qos = QoSProfile(
            depth=500,
            durability=DurabilityPolicy.VOLATILE,
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
        )

        self.pub = self.create_publisher(TFMessage, target_topic, qos)
        self.sub = self.create_subscription(TFMessage, '/tf', self.callback, qos)
        self.get_logger().info(f'tf_relay: /tf → {target_topic}')

    def callback(self, msg: TFMessage):
        self.pub.publish(msg)


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else '/tf_relay_out'
    rclpy.init()
    node = TFRelay(target)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
