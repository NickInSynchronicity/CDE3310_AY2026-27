#!/usr/bin/env python3
"""
map_relay.py

Relays /map to /{ns}/map with TRANSIENT_LOCAL durability, buffering the
last received map so that late-joining subscribers (like the global costmap
static_layer) always receive it immediately on connection.

topic_tools relay does NOT buffer TRANSIENT_LOCAL messages. If slam_toolbox
publishes /map before the global_costmap subscribes to /{ns}/map, the costmap
misses it entirely and logs "Can't update static costmap layer, no map received"
until the next publish cycle (every 5s). This relay stores the latest map and
re-publishes it to every new subscriber immediately via TRANSIENT_LOCAL.

Usage: python3 map_relay.py <target_topic>
  e.g. python3 map_relay.py /tb3_2/map
"""

import sys
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy
from nav_msgs.msg import OccupancyGrid


class MapRelay(Node):
    def __init__(self, target_topic):
        super().__init__('map_relay')

        transient_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
        )

        self.pub = self.create_publisher(OccupancyGrid, target_topic, transient_qos)

        # Subscribe with TRANSIENT_LOCAL so we receive slam_toolbox's map
        # even if it was published before we started.
        self.sub = self.create_subscription(
            OccupancyGrid, '/map', self.callback, transient_qos
        )

        self.get_logger().info(
            f'map_relay: /map → {target_topic} (TRANSIENT_LOCAL, buffered)'
        )

    def callback(self, msg: OccupancyGrid):
        # Refresh the stamp to now before re-publishing.
        # The cached TRANSIENT_LOCAL message may carry a stale header.stamp
        # from a previous session. Forwarding an old stamp causes the
        # global_costmap's StaticLayer to request TF lookups at that old
        # time, which may fall outside the TF buffer and stall activation.
        msg.header.stamp = self.get_clock().now().to_msg()
        self.pub.publish(msg)
        self.get_logger().debug(
            f'map_relay: forwarded map {msg.info.width}x{msg.info.height} '
            f'frame={msg.header.frame_id}'
        )


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else '/map_relay_out'
    rclpy.init()
    node = MapRelay(target)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()