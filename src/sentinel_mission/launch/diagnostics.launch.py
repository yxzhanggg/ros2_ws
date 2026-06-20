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
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    diagnostic_period = LaunchConfiguration('diagnostic_period')

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'diagnostic_period',
                default_value='1.0',
                description='Diagnostic updater publish period in seconds.',
            ),
            Node(
                package='sentinel_mission',
                executable='health_monitor',
                name='health_monitor',
                output='screen',
                parameters=[{'diagnostic_period': diagnostic_period}],
            ),
        ]
    )
