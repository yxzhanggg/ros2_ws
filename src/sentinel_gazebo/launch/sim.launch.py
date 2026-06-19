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
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    world_file = LaunchConfiguration('world_file')
    xacro_file = LaunchConfiguration('xacro_file')

    default_world_file = PathJoinSubstitution(
        [FindPackageShare('sentinel_gazebo'), 'worlds', 'sentinel_warehouse.sdf']
    )
    default_xacro_file = PathJoinSubstitution(
        [FindPackageShare('sentinel_description'), 'urdf', 'sentinel.urdf.xacro']
    )
    bridge_config = PathJoinSubstitution(
        [FindPackageShare('sentinel_gazebo'), 'config', 'bridge.yaml']
    )
    gz_launch = PathJoinSubstitution(
        [FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py']
    )

    robot_description = {
        'robot_description': ParameterValue(
            Command(['xacro ', xacro_file, ' use_sim:=', use_sim_time]),
            value_type=str,
        )
    }

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'use_sim_time',
                default_value='true',
                description='Use Gazebo simulation clock.',
            ),
            DeclareLaunchArgument(
                'world_file',
                default_value=default_world_file,
                description='Path to the Gazebo world file.',
            ),
            DeclareLaunchArgument(
                'xacro_file',
                default_value=default_xacro_file,
                description='Path to the Nexus Sentinel Xacro model.',
            ),
            DeclareLaunchArgument(
                'headless',
                default_value='true',
                description='Run Gazebo server only when true.',
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(gz_launch),
                launch_arguments={
                    'gz_args': ['-r -s ', world_file],
                    'gz_version': '10',
                }.items(),
            ),
            Node(
                package='robot_state_publisher',
                executable='robot_state_publisher',
                name='robot_state_publisher',
                output='screen',
                parameters=[robot_description, {'use_sim_time': use_sim_time}],
            ),
            Node(
                package='ros_gz_sim',
                executable='create',
                arguments=[
                    '-world',
                    'sentinel_warehouse',
                    '-name',
                    'nexus_sentinel',
                    '-topic',
                    'robot_description',
                    '-x',
                    '0.0',
                    '-y',
                    '0.0',
                    '-z',
                    '0.18',
                    '-allow_renaming',
                    'false',
                ],
                output='screen',
            ),
            Node(
                package='ros_gz_bridge',
                executable='parameter_bridge',
                name='sentinel_gz_bridge',
                parameters=[{'config_file': bridge_config}],
                output='screen',
            ),
        ]
    )
