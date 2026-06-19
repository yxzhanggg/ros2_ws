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
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    controller_manager = LaunchConfiguration('controller_manager')
    controller_config = LaunchConfiguration('controller_config')

    default_controller_config = PathJoinSubstitution(
        [FindPackageShare('sentinel_control'), 'config', 'controllers.yaml']
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'controller_manager',
                default_value='/controller_manager',
                description='Controller manager service namespace.',
            ),
            DeclareLaunchArgument(
                'controller_config',
                default_value=default_controller_config,
                description='ros2_control controller parameter file.',
            ),
            Node(
                package='controller_manager',
                executable='spawner',
                arguments=[
                    'joint_state_broadcaster',
                    '--controller-manager',
                    controller_manager,
                    '--param-file',
                    controller_config,
                ],
                output='screen',
            ),
            Node(
                package='controller_manager',
                executable='spawner',
                arguments=[
                    'diff_drive_controller',
                    '--controller-manager',
                    controller_manager,
                    '--param-file',
                    controller_config,
                ],
                output='screen',
            ),
            Node(
                package='controller_manager',
                executable='spawner',
                arguments=[
                    'imu_sensor_broadcaster',
                    '--controller-manager',
                    controller_manager,
                    '--param-file',
                    controller_config,
                ],
                output='screen',
            ),
        ]
    )
