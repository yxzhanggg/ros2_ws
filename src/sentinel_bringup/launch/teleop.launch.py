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
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    start_sim = LaunchConfiguration('start_sim')
    headless = LaunchConfiguration('headless')
    cmd_vel_topic = LaunchConfiguration('cmd_vel_topic')
    start_joy = LaunchConfiguration('start_joy')

    sim_launch = PathJoinSubstitution(
        [FindPackageShare('sentinel_gazebo'), 'launch', 'sim.launch.py']
    )
    gamepad_launch = PathJoinSubstitution(
        [FindPackageShare('sentinel_teleop'), 'launch', 'gamepad.launch.py']
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'start_sim',
                default_value='true',
                description='Start the Gazebo simulation and controllers.',
            ),
            DeclareLaunchArgument(
                'headless',
                default_value='true',
                description='Run Gazebo in server-only mode.',
            ),
            DeclareLaunchArgument(
                'cmd_vel_topic',
                default_value='/diff_drive_controller/cmd_vel',
                description='Teleop command topic.',
            ),
            DeclareLaunchArgument(
                'start_joy',
                default_value='true',
                description='Start joy_node. Set false for synthetic /joy tests.',
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(sim_launch),
                launch_arguments={
                    'headless': headless,
                    'spawn_controllers': 'true',
                }.items(),
                condition=IfCondition(start_sim),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(gamepad_launch),
                launch_arguments={
                    'cmd_vel_topic': cmd_vel_topic,
                    'start_joy': start_joy,
                }.items(),
            ),
        ]
    )
