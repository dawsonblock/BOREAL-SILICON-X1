import rclpy
from rclpy.lifecycle import Node, State, TransitionCallbackReturn
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
import struct
import time
import spidev
import math

# Import SipHash and ChaCha20
from siphash import siphash24
from chacha20 import chacha20_encrypt


class BorealBridge(Node):
    def __init__(self):
        super().__init__("boreal_bridge")
        self.get_logger().info("BorealBridge: __init__")

        # Declare member variables that will be initialized in on_configure
        self.subscription = None
        self.odom_publisher = None
        self.tf_broadcaster = None
        self.spi = None
        self.MAC_KEY = None
        self.CHACHA_KEY = None
        self.SEQ = 0
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.vtheta = 0.0
        self.timer = None

    def on_configure(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info("BorealBridge: on_configure")

        # QoS Profiles
        qos_profile_reliable = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        qos_profile_sensor_data = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        # Subscribers
        self.subscription = self.create_subscription(
            Twist, "/cmd_vel", self.cmd_vel_callback, qos_profile_reliable
        )

        # Publishers
        self.odom_publisher = self.create_lifecycle_publisher(
            Odometry, "/odom", qos_profile_sensor_data
        )
        self.tf_broadcaster = TransformBroadcaster(self)

        # SPI Setup (from ai_agent.py)
        self.MAC_KEY = struct.pack("<QQ", 0xA3B1C2D3E4F56789, 0x1020304050607080)
        self.CHACHA_KEY = struct.pack(
            "<8I",
            0x01020304,
            0x05060708,
            0x090A0B0C,
            0x0D0E0F10,
            0x11121314,
            0x15161718,
            0x191A1B1C,
            0x1D1E1F20,
        )
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 10_000_000
        self.spi.mode = 0
        self.SEQ = 0

        # Odom state (stub - no encoders yet)
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.vtheta = 0.0

        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info("BorealBridge: on_activate")
        # Timer for odom publishing
        self.timer = self.create_timer(0.05, self.publish_odom)  # 20 Hz
        return TransitionCallbackReturn.SUCCESS

    def on_deactivate(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info("BorealBridge: on_deactivate")
        if self.timer:
            self.destroy_timer(self.timer)
            self.timer = None
        return TransitionCallbackReturn.SUCCESS

    def on_cleanup(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info("BorealBridge: on_cleanup")
        self.destroy_subscription(self.subscription)
        self.destroy_publisher(self.odom_publisher)
        del self.tf_broadcaster  # TransformBroadcaster doesn't have a destroy method
        if self.spi:
            self.spi.close()
        return TransitionCallbackReturn.SUCCESS

    def on_shutdown(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info("BorealBridge: on_shutdown")
        return TransitionCallbackReturn.SUCCESS

    def cmd_vel_callback(self, msg):
        # Convert Twist to intent
        # Simple mapping: linear.x -> speed, angular.z -> turn
        intent_id = 2  # FORWARD by default
        speed = int(msg.linear.x * 1000)  # Scale to some units
        turn = int(msg.angular.z * 100)  # Scale

        # Clamp to bounds
        speed = max(-8000, min(8000, speed))
        turn = max(-30, min(30, turn))

        # For simplicity, send as intent 2 (FORWARD) with value = speed
        # If turn != 0, perhaps send intent 3 (TURN) with turn value
        if abs(turn) > 0:
            intent_id = 3  # TURN_LEFT or TURN_RIGHT, but policy has TURN_LEFT
            value = turn
        else:
            intent_id = 2  # FORWARD
            value = speed

        # Confidence: assume high
        conf_q15 = 32767  # Max Q15

        # Send to Boreal
        self.send_to_boreal(intent_id, conf_q15, [value])

        # Update odom estimate (dead reckoning)
        dt = 0.05
        self.vx = msg.linear.x
        self.vtheta = msg.angular.z
        self.x += self.vx * dt * math.cos(self.theta)
        self.y += self.vx * dt * math.sin(self.theta)
        self.theta += self.vtheta * dt

    def send_to_boreal(self, intent_id, conf_q15, aux_data):
        self.SEQ += 1

        # Encrypt-then-MAC payload
        aux = (aux_data + [0] * 18)[:18]  # Pad to 18 elements

        plaintext = struct.pack("<HH18h", intent_id, conf_q15, *aux)
        ciphertext = chacha20_encrypt(plaintext, self.CHACHA_KEY, self.SEQ, 0)

        header = struct.pack(
            "<IHHII", 0xB0A1E1A1, 1, 1, self.SEQ, int(time.time() * 1000) & 0xFFFFFFFF
        )

        payload = header + ciphertext

        # Cryptographic MAC + SPI Frame
        mac = siphash24(self.MAC_KEY, payload)
        frame = bytes([0x01, 64]) + payload + mac
        self.spi.xfer2(list(frame))

    def publish_odom(self):
        # Publish odometry (stub implementation)
        msg = Odometry()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "odom"
        msg.child_frame_id = "base_link"

        msg.pose.pose.position.x = self.x
        msg.pose.pose.position.y = self.y
        msg.pose.pose.orientation.z = math.sin(self.theta / 2)
        msg.pose.pose.orientation.w = math.cos(self.theta / 2)

        msg.twist.twist.linear.x = self.vx
        msg.twist.twist.angular.z = self.vtheta

        if self.odom_publisher is not None and self.odom_publisher.is_activated:
            self.odom_publisher.publish(msg)

        # Broadcast transform
        t = TransformStamped()
        t.header = msg.header
        t.child_frame_id = msg.child_frame_id
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.rotation = msg.pose.pose.orientation
        self.tf_broadcaster.sendTransform(t)


def main(args=None):
    rclpy.init(args=args)
    bridge = BorealBridge()

    # Simple auto-transition execution for standalone running
    try:
        bridge.trigger_configure()
        bridge.trigger_activate()
        rclpy.spin(bridge)
    except KeyboardInterrupt:
        pass
    finally:
        bridge.trigger_deactivate()
        bridge.trigger_cleanup()
        bridge.trigger_shutdown()
        bridge.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
