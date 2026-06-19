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
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    log_path = LaunchConfiguration('log_path')
    mission_launch = PathJoinSubstitution(
        [FindPackageShare('sentinel_mission'), 'launch', 'mission.launch.py']
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'log_path',
                default_value='log/mission_events.jsonl',
                description='Mission logger JSONL output path.',
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(mission_launch),
                launch_arguments={'log_path': log_path}.items(),
            ),
        ]
    )
