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
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LifecycleNode, Node
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState
from lifecycle_msgs.msg import Transition


def generate_launch_description():
    log_path = LaunchConfiguration('log_path')
    start_health_monitor = LaunchConfiguration('start_health_monitor')

    mode_manager = LifecycleNode(
        package='sentinel_mission',
        executable='mode_manager',
        name='mode_manager',
        namespace='',
        output='screen',
    )

    configure_mode_manager = RegisterEventHandler(
        OnProcessStart(
            target_action=mode_manager,
            on_start=[
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=matches_action(mode_manager),
                        transition_id=Transition.TRANSITION_CONFIGURE,
                    )
                )
            ],
        )
    )

    activate_mode_manager = RegisterEventHandler(
        OnStateTransition(
            target_lifecycle_node=mode_manager,
            goal_state='inactive',
            entities=[
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=matches_action(mode_manager),
                        transition_id=Transition.TRANSITION_ACTIVATE,
                    )
                )
            ],
        )
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'log_path',
                default_value='log/mission_events.jsonl',
                description='Mission logger JSONL output path.',
            ),
            DeclareLaunchArgument(
                'start_health_monitor',
                default_value='true',
                description='Start Phase 9 diagnostic health monitor.',
            ),
            mode_manager,
            configure_mode_manager,
            activate_mode_manager,
            Node(
                package='sentinel_mission',
                executable='mission_logger',
                name='mission_logger',
                output='screen',
                parameters=[{'log_path': log_path}],
            ),
            Node(
                package='sentinel_mission',
                executable='health_monitor',
                name='health_monitor',
                output='screen',
                condition=IfCondition(start_health_monitor),
            ),
        ]
    )
