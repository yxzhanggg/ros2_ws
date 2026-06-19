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

from sentinel_interfaces.msg import RoverMode
from sentinel_teleop.gamepad_interface import compute_teleop_output
from sentinel_teleop.gamepad_interface import TeleopConfig


def _config() -> TeleopConfig:
    return TeleopConfig(
        deadzone=0.08,
        max_linear_velocity=0.5,
        max_angular_velocity=1.0,
        linear_axis=1,
        angular_axis=3,
        speed_axis=5,
        deadman_button=4,
        teleop_button=0,
        mapping_button=3,
        patrol_button=1,
        estop_button=2,
        clear_estop_button=5,
        record_button=8,
        stop_record_button=9,
        frame_id='base_footprint',
    )


def test_deadman_released_forces_zero_command():
    axes = [0.0, -1.0, 0.0, -1.0, 0.0, -1.0]
    buttons = [0] * 13

    output = compute_teleop_output(axes, buttons, _config(), False)

    assert output.linear_x == 0.0
    assert output.angular_z == 0.0


def test_deadman_pressed_scales_command_with_trigger():
    axes = [0.0, -1.0, 0.0, -0.5, 0.0, -1.0]
    buttons = [0] * 13
    buttons[4] = 1

    output = compute_teleop_output(axes, buttons, _config(), False)

    assert output.linear_x == 0.5
    assert output.angular_z == 0.5


def test_estop_latches_until_clear_button():
    buttons = [0] * 13
    buttons[2] = 1

    output = compute_teleop_output([0.0] * 8, buttons, _config(), False)

    assert output.estop_locked is True
    assert output.mode == RoverMode.MODE_ESTOP

    buttons[2] = 0
    output = compute_teleop_output([0.0] * 8, buttons, _config(), True)

    assert output.estop_locked is True

    buttons[5] = 1
    output = compute_teleop_output([0.0] * 8, buttons, _config(), True)

    assert output.estop_locked is False


def test_mode_buttons_and_record_edges_are_detected():
    buttons = [0] * 13
    buttons[3] = 1
    buttons[8] = 1

    output = compute_teleop_output([0.0] * 8, buttons, _config(), False)

    assert output.mode == RoverMode.MODE_MAPPING
    assert output.record_requested is True
    assert output.stop_record_requested is False
