# Copyright 2026 yxzhanggg
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""DualSense joystick to Nexus Sentinel teleoperation commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast, Iterable, Optional

from geometry_msgs.msg import TwistStamped
from rcl_interfaces.msg import SetParametersResult
import rclpy
from rclpy.lifecycle import LifecycleNode
from rclpy.lifecycle import LifecycleState
from rclpy.lifecycle import TransitionCallbackReturn
from rclpy.lifecycle.publisher import LifecyclePublisher
from rclpy.parameter import Parameter
from rclpy.qos import QoSProfile
from rclpy.subscription import Subscription
from sensor_msgs.msg import Joy
from sentinel_interfaces.msg import RoverMode
from std_msgs.msg import Bool


MODE_LABELS = {
    RoverMode.MODE_TELEOP: 'TELEOP',
    RoverMode.MODE_MAPPING: 'MAPPING',
    RoverMode.MODE_PATROL: 'PATROL',
    RoverMode.MODE_ESTOP: 'ESTOP',
}


@dataclass(frozen=True)
class TeleopConfig:
    """Runtime-adjustable gamepad mapping and limits."""

    deadzone: float
    max_linear_velocity: float
    max_angular_velocity: float
    linear_axis: int
    angular_axis: int
    speed_axis: int
    deadman_button: int
    teleop_button: int
    mapping_button: int
    patrol_button: int
    estop_button: int
    clear_estop_button: int
    record_button: int
    stop_record_button: int
    frame_id: str


@dataclass(frozen=True)
class TeleopOutput:
    """Pure translation result, kept separate for unit tests."""

    linear_x: float
    angular_z: float
    mode: int | None
    estop_locked: bool
    record_requested: bool
    stop_record_requested: bool


def _axis(axes: Iterable[float], index: int, default: float = 0.0) -> float:
    axes_list = list(axes)
    if index < 0 or index >= len(axes_list):
        return default
    return float(axes_list[index])


def _button(buttons: Iterable[int], index: int) -> bool:
    buttons_list = list(buttons)
    return 0 <= index < len(buttons_list) and bool(buttons_list[index])


def _apply_deadzone(value: float, deadzone: float) -> float:
    if abs(value) <= deadzone:
        return 0.0
    return value


def compute_teleop_output(
    axes: Iterable[float],
    buttons: Iterable[int],
    config: TeleopConfig,
    previous_estop_locked: bool,
) -> TeleopOutput:
    """Convert a Joy sample into command, mode, and lock state."""
    estop_locked = previous_estop_locked or _button(buttons, config.estop_button)
    if _button(buttons, config.clear_estop_button):
        estop_locked = False

    mode: int | None = None
    if _button(buttons, config.teleop_button):
        mode = RoverMode.MODE_TELEOP
    elif _button(buttons, config.mapping_button):
        mode = RoverMode.MODE_MAPPING
    elif _button(buttons, config.patrol_button):
        mode = RoverMode.MODE_PATROL
    elif _button(buttons, config.estop_button):
        mode = RoverMode.MODE_ESTOP

    linear_axis_value = -_apply_deadzone(
        _axis(axes, config.linear_axis), config.deadzone
    )
    angular_axis_value = -_apply_deadzone(
        _axis(axes, config.angular_axis), config.deadzone
    )
    speed_axis_value = _axis(axes, config.speed_axis, default=-1.0)
    speed_scale = max(0.0, min(1.0, (1.0 - speed_axis_value) * 0.5))

    deadman_pressed = _button(buttons, config.deadman_button)
    if estop_locked or not deadman_pressed:
        linear_x = 0.0
        angular_z = 0.0
    else:
        linear_x = linear_axis_value * config.max_linear_velocity * speed_scale
        angular_z = angular_axis_value * config.max_angular_velocity * speed_scale

    return TeleopOutput(
        linear_x=linear_x,
        angular_z=angular_z,
        mode=mode,
        estop_locked=estop_locked,
        record_requested=_button(buttons, config.record_button),
        stop_record_requested=_button(buttons, config.stop_record_button),
    )


class GamepadInterface(LifecycleNode):
    """Lifecycle node that maps DualSense input to teleoperation topics."""

    def __init__(self) -> None:
        super().__init__('gamepad_interface')
        self._configured = False
        self._active = False
        self._estop_locked = False
        self._last_record_request = False
        self._last_stop_record_request = False

        self._declare_parameters()
        self._config = self._read_config()
        self.add_on_set_parameters_callback(self._on_parameters_changed)

        self._joy_sub: Optional[Subscription[Joy]] = None
        self._cmd_pub: Optional[LifecyclePublisher[TwistStamped]] = None
        self._lock_pub: Optional[LifecyclePublisher[Bool]] = None
        self._mode_pub: Optional[LifecyclePublisher[RoverMode]] = None
        self._record_request_pub: Optional[LifecyclePublisher[Bool]] = None
        self._stop_record_request_pub: Optional[LifecyclePublisher[Bool]] = None

    def _declare_parameters(self) -> None:
        defaults = {
            'deadzone': 0.08,
            'max_linear_velocity': 0.45,
            'max_angular_velocity': 1.3,
            'linear_axis': 1,
            'angular_axis': 3,
            'speed_axis': 5,
            'deadman_button': 4,
            'teleop_button': 0,
            'mapping_button': 3,
            'patrol_button': 1,
            'estop_button': 2,
            'clear_estop_button': 5,
            'record_button': 8,
            'stop_record_button': 9,
            'frame_id': 'base_footprint',
        }
        for name, value in defaults.items():
            self.declare_parameter(name, value)

    def _read_config(self) -> TeleopConfig:
        return TeleopConfig(
            deadzone=float(self.get_parameter('deadzone').value),
            max_linear_velocity=float(
                self.get_parameter('max_linear_velocity').value
            ),
            max_angular_velocity=float(
                self.get_parameter('max_angular_velocity').value
            ),
            linear_axis=int(self.get_parameter('linear_axis').value),
            angular_axis=int(self.get_parameter('angular_axis').value),
            speed_axis=int(self.get_parameter('speed_axis').value),
            deadman_button=int(self.get_parameter('deadman_button').value),
            teleop_button=int(self.get_parameter('teleop_button').value),
            mapping_button=int(self.get_parameter('mapping_button').value),
            patrol_button=int(self.get_parameter('patrol_button').value),
            estop_button=int(self.get_parameter('estop_button').value),
            clear_estop_button=int(
                self.get_parameter('clear_estop_button').value
            ),
            record_button=int(self.get_parameter('record_button').value),
            stop_record_button=int(
                self.get_parameter('stop_record_button').value
            ),
            frame_id=str(self.get_parameter('frame_id').value),
        )

    def _on_parameters_changed(
        self, parameters: list[Parameter]
    ) -> SetParametersResult:
        current = self._read_config()
        proposed = {
            'deadzone': current.deadzone,
            'max_linear_velocity': current.max_linear_velocity,
            'max_angular_velocity': current.max_angular_velocity,
            'linear_axis': current.linear_axis,
            'angular_axis': current.angular_axis,
            'speed_axis': current.speed_axis,
            'deadman_button': current.deadman_button,
            'teleop_button': current.teleop_button,
            'mapping_button': current.mapping_button,
            'patrol_button': current.patrol_button,
            'estop_button': current.estop_button,
            'clear_estop_button': current.clear_estop_button,
            'record_button': current.record_button,
            'stop_record_button': current.stop_record_button,
            'frame_id': current.frame_id,
        }
        for parameter in parameters:
            proposed[parameter.name] = parameter.value

        reason = self._validate_config_values(proposed)
        if reason:
            return SetParametersResult(successful=False, reason=reason)

        self._config = self._dict_to_config(proposed)
        return SetParametersResult(successful=True)

    def _validate_config_values(self, values: dict[str, object]) -> str:
        config = self._dict_to_config(values)
        if not 0.0 <= config.deadzone <= 0.5:
            return 'deadzone must be in [0.0, 0.5]'
        if not 0.0 < config.max_linear_velocity <= 1.5:
            return 'max_linear_velocity must be in (0.0, 1.5]'
        if not 0.0 < config.max_angular_velocity <= 3.5:
            return 'max_angular_velocity must be in (0.0, 3.5]'
        non_negative_values = {
            'linear_axis': config.linear_axis,
            'angular_axis': config.angular_axis,
            'speed_axis': config.speed_axis,
            'deadman_button': config.deadman_button,
            'teleop_button': config.teleop_button,
            'mapping_button': config.mapping_button,
            'patrol_button': config.patrol_button,
            'estop_button': config.estop_button,
            'clear_estop_button': config.clear_estop_button,
            'record_button': config.record_button,
            'stop_record_button': config.stop_record_button,
        }
        for key, value in non_negative_values.items():
            if value < 0:
                return f'{key} must be non-negative'
        if not config.frame_id:
            return 'frame_id must not be empty'
        return ''

    def _dict_to_config(self, values: dict[str, object]) -> TeleopConfig:
        return TeleopConfig(
            deadzone=float(cast(float, values['deadzone'])),
            max_linear_velocity=float(
                cast(float, values['max_linear_velocity'])
            ),
            max_angular_velocity=float(
                cast(float, values['max_angular_velocity'])
            ),
            linear_axis=int(cast(int, values['linear_axis'])),
            angular_axis=int(cast(int, values['angular_axis'])),
            speed_axis=int(cast(int, values['speed_axis'])),
            deadman_button=int(cast(int, values['deadman_button'])),
            teleop_button=int(cast(int, values['teleop_button'])),
            mapping_button=int(cast(int, values['mapping_button'])),
            patrol_button=int(cast(int, values['patrol_button'])),
            estop_button=int(cast(int, values['estop_button'])),
            clear_estop_button=int(cast(int, values['clear_estop_button'])),
            record_button=int(cast(int, values['record_button'])),
            stop_record_button=int(cast(int, values['stop_record_button'])),
            frame_id=str(cast(str, values['frame_id'])),
        )

    def on_configure(self, state: LifecycleState) -> TransitionCallbackReturn:
        """Create ROS interfaces when the lifecycle node is configured."""
        del state
        qos = QoSProfile(depth=10)
        self._cmd_pub = self.create_lifecycle_publisher(
            TwistStamped, 'cmd_vel_teleop', qos
        )
        self._lock_pub = self.create_lifecycle_publisher(
            Bool, 'cmd_vel_lock', qos
        )
        self._mode_pub = self.create_lifecycle_publisher(
            RoverMode, 'rover_mode_request', qos
        )
        self._record_request_pub = self.create_lifecycle_publisher(
            Bool, 'record_request', qos
        )
        self._stop_record_request_pub = self.create_lifecycle_publisher(
            Bool, 'stop_record_request', qos
        )
        self._joy_sub = self.create_subscription(
            Joy, 'joy', self._on_joy, QoSProfile(depth=10)
        )
        self._configured = True
        self.get_logger().info('Gamepad interface configured')
        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state: LifecycleState) -> TransitionCallbackReturn:
        """Enable Joy samples to publish teleoperation outputs."""
        self._active = True
        self.get_logger().info('Gamepad interface activated')
        return super().on_activate(state)

    def on_deactivate(self, state: LifecycleState) -> TransitionCallbackReturn:
        """Publish a zero command and stop processing Joy samples."""
        self._active = False
        self._publish_zero()
        self.get_logger().info('Gamepad interface deactivated')
        return super().on_deactivate(state)

    def on_cleanup(self, state: LifecycleState) -> TransitionCallbackReturn:
        """Release ROS interfaces created during configuration."""
        del state
        self._configured = False
        self._active = False
        if self._joy_sub is not None:
            self.destroy_subscription(self._joy_sub)
        self._joy_sub = None
        self._cmd_pub = None
        self._lock_pub = None
        self._mode_pub = None
        self._record_request_pub = None
        self._stop_record_request_pub = None
        return TransitionCallbackReturn.SUCCESS

    def _on_joy(self, msg: Joy) -> None:
        if not self._configured or not self._active:
            return
        output = compute_teleop_output(
            msg.axes, msg.buttons, self._config, self._estop_locked
        )
        self._estop_locked = output.estop_locked
        self._publish_command(output.linear_x, output.angular_z)
        self._publish_lock(output.estop_locked)
        if output.mode is not None:
            self._publish_mode(output.mode)
        self._publish_record_edges(output)

    def _publish_command(self, linear_x: float, angular_z: float) -> None:
        command = TwistStamped()
        command.header.stamp = self.get_clock().now().to_msg()
        command.header.frame_id = self._config.frame_id
        command.twist.linear.x = linear_x
        command.twist.angular.z = angular_z
        if self._cmd_pub is not None:
            self._cmd_pub.publish(command)

    def _publish_zero(self) -> None:
        if self._cmd_pub is not None:
            self._publish_command(0.0, 0.0)

    def _publish_lock(self, locked: bool) -> None:
        lock = Bool()
        lock.data = locked
        if self._lock_pub is not None:
            self._lock_pub.publish(lock)

    def _publish_mode(self, mode: int) -> None:
        mode_msg = RoverMode()
        mode_msg.mode = mode
        mode_msg.mode_label = MODE_LABELS.get(mode, 'UNKNOWN')
        mode_msg.stamp = self.get_clock().now().to_msg()
        if self._mode_pub is not None:
            self._mode_pub.publish(mode_msg)

    def _publish_record_edges(self, output: TeleopOutput) -> None:
        if output.record_requested and not self._last_record_request:
            msg = Bool()
            msg.data = True
            if self._record_request_pub is not None:
                self._record_request_pub.publish(msg)
            self.get_logger().info('Record start requested')
        if output.stop_record_requested and not self._last_stop_record_request:
            msg = Bool()
            msg.data = True
            if self._stop_record_request_pub is not None:
                self._stop_record_request_pub.publish(msg)
            self.get_logger().info('Record stop requested')
        self._last_record_request = output.record_requested
        self._last_stop_record_request = output.stop_record_requested


def main(args: list[str] | None = None) -> None:
    """Run the gamepad interface lifecycle node."""
    rclpy.init(args=args)
    node = GamepadInterface()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
