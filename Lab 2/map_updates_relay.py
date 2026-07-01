#!/usr/bin/env python3
"""
map_updates_relay.py

Relays /map_updates to /{ns}/map_updates so that RViz's Map display
receives incremental map updates from slam_toolbox in real time.

slam_toolbox publishes two topics:
  /map          — full OccupancyGrid every map_update_interval seconds
  /map_updates  — incremental OccupancyGridUpdate after every processed scan

map_relay.py handles /map → /{ns}/map (TRANSIENT_LOCAL).
This script handles /map_updates → /{ns}/map_updates (VOLATILE).
Without this relay, RViz only sees the full map every 2s and misses
all incremental updates, making the map appear frozen between full publishes.

Usage: python3 map_updates_relay.py <target_topic>
  e.g. python3 map_updates_relay.py /tb3_2/map_updates
"""

import sys
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy
from map_msgs.msg import OccupancyGridUpdate


class MapUpdatesRelay(Node):
    def __init__(self, target_topic):
        super().__init__('map_updates_relay')

        qos = QoSProfile(
            depth=10,
            durability=DurabilityPolicy.VOLATILE,
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
        )

        self.pub = self.create_publisher(OccupancyGridUpdate, target_topic, qos)
        self.sub = self.create_subscription(
            OccupancyGridUpdate, '/map_updates', self.callback, qos
        )
        self.get_logger().info(f'map_updates_relay: /map_updates → {target_topic}')

    def callback(self, msg: OccupancyGridUpdate):
        self.pub.publish(msg)


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else '/map_updates_relay_out'
    rclpy.init()
    node = MapUpdatesRelay(target)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
