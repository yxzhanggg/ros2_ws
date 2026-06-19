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

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessStart
from launch.events import matches_action
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import LifecycleNode, Node
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState
from launch_ros.substitutions import FindPackageShare
from lifecycle_msgs.msg import Transition


def generate_launch_description():
    joy_device_id = LaunchConfiguration('joy_device_id')
    joy_deadzone = LaunchConfiguration('joy_deadzone')
    joy_autorepeat_rate = LaunchConfiguration('joy_autorepeat_rate')
    gamepad_config = LaunchConfiguration('gamepad_config')
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')
    start_joy = LaunchConfiguration('start_joy')

    default_gamepad_config = PathJoinSubstitution(
        [FindPackageShare('sentinel_teleop'), 'config', 'gamepad.yaml']
    )

    gamepad_node = LifecycleNode(
        package='sentinel_teleop',
        executable='gamepad_interface',
        name='gamepad_interface',
        namespace='',
        output='screen',
        parameters=[gamepad_config],
        remappings=[
            ('cmd_vel_teleop', cmd_vel_topic),
        ],
    )

    configure_gamepad = RegisterEventHandler(
        OnProcessStart(
            target_action=gamepad_node,
            on_start=[
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=matches_action(gamepad_node),
                        transition_id=Transition.TRANSITION_CONFIGURE,
                    )
                )
            ],
        )
    )

    activate_gamepad = RegisterEventHandler(
        OnStateTransition(
            target_lifecycle_node=gamepad_node,
            goal_state='inactive',
            entities=[
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=matches_action(gamepad_node),
                        transition_id=Transition.TRANSITION_ACTIVATE,
                    )
                )
            ],
        )
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'joy_device_id',
                default_value='0',
                description='Joystick device id for the DualSense controller.',
            ),
            DeclareLaunchArgument(
                'joy_deadzone',
                default_value='0.05',
                description='Low-level joy_node deadzone before project filtering.',
            ),
            DeclareLaunchArgument(
                'joy_autorepeat_rate',
                default_value='20.0',
                description='joy_node repeat rate in Hz.',
            ),
            DeclareLaunchArgument(
                'gamepad_config',
                default_value=default_gamepad_config,
                description='Gamepad interface parameter file.',
            ),
            DeclareLaunchArgument(
                'cmd_vel_topic',
                default_value='/diff_drive_controller/cmd_vel',
                description='Stamped velocity command topic for the active controller.',
            ),
            DeclareLaunchArgument(
                'start_joy',
                default_value='true',
                description='Start joy_node. Set false for synthetic /joy tests.',
            ),
            Node(
                package='joy',
                executable='joy_node',
                name='joy_node',
                output='screen',
                parameters=[
                    {
                        'device_id': joy_device_id,
                        'deadzone': joy_deadzone,
                        'autorepeat_rate': joy_autorepeat_rate,
                    }
                ],
                condition=IfCondition(start_joy),
            ),
            gamepad_node,
            configure_gamepad,
            activate_gamepad,
        ]
    )
