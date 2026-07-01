#!/usr/bin/env python3
"""
tf_static_relay.py

Relays /tf_static to /{ns}/tf_static with TRANSIENT_LOCAL durability.

topic_tools relay uses VOLATILE durability. Static TFs are published with
TRANSIENT_LOCAL (latched). Nav2 nodes that start after the relay has already
forwarded the static TFs will never receive them with a VOLATILE relay.
This node accumulates all static transforms and re-publishes the complete
set with TRANSIENT_LOCAL so late-joining subscribers always get them.

Usage: python3 tf_static_relay.py <target_topic>
  e.g. python3 tf_static_relay.py /tb3_2/tf_static
"""

import sys
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy
from tf2_msgs.msg import TFMessage


class TFStaticRelay(Node):
    def __init__(self, target_topic):
        super().__init__('tf_static_relay')

        transient_qos = QoSProfile(
            depth=100,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
        )

        self.pub = self.create_publisher(TFMessage, target_topic, transient_qos)
        self.sub = self.create_subscription(
            TFMessage, '/tf_static', self.callback, transient_qos
        )
        # Key: (parent_frame, child_frame) → latest transform
        # Accumulating ensures late-joining subscribers always get the full set.
        self._transforms = {}
        self.get_logger().info(
            f'tf_static_relay: /tf_static → {target_topic} (TRANSIENT_LOCAL)'
        )

    def callback(self, msg: TFMessage):
        for t in msg.transforms:
            key = (t.header.frame_id, t.child_frame_id)
            self._transforms[key] = t
        out = TFMessage()
        out.transforms = list(self._transforms.values())
        self.pub.publish(out)


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else '/tf_static_relay_out'
    rclpy.init()
    node = TFStaticRelay(target)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()