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

from ament_index_python.packages import get_package_share_directory, PackageNotFoundError
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import EmitEvent
from launch.actions import IncludeLaunchDescription
from launch.actions import LogInfo
from launch.actions import OpaqueFunction
from launch.conditions import IfCondition
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def _missing_packages(package_names):
    missing = []
    for package_name in package_names:
        try:
            get_package_share_directory(package_name)
        except PackageNotFoundError:
            missing.append(package_name)
    return missing


def _launch_setup(context, *args, **kwargs):
    del args
    del kwargs

    required_packages = ['nav2_bringup', 'nav2_msgs', 'twist_mux']
    missing = _missing_packages(required_packages)
    if missing:
        return [
            LogInfo(
                msg=[
                    'Phase 7 navigation dependencies are missing: ',
                    ', '.join(missing),
                    '. Install the matching ROS Lyrical packages, then rerun this launch.',
                ]
            ),
            EmitEvent(event=Shutdown(reason='missing Phase 7 navigation dependencies')),
        ]

    headless = LaunchConfiguration('headless')
    start_sim = LaunchConfiguration('start_sim')
    start_mission = LaunchConfiguration('start_mission')
    nav_params = LaunchConfiguration('nav_params')
    map_file = LaunchConfiguration('map')
    twist_mux_params = LaunchConfiguration('twist_mux_params')

    sim_launch = PathJoinSubstitution(
        [FindPackageShare('sentinel_gazebo'), 'launch', 'sim.launch.py']
    )
    mission_launch = PathJoinSubstitution(
        [FindPackageShare('sentinel_mission'), 'launch', 'mission.launch.py']
    )
    nav2_launch = PathJoinSubstitution(
        [FindPackageShare('nav2_bringup'), 'launch', 'bringup_launch.py']
    )

    return [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(sim_launch),
            launch_arguments={
                'headless': headless,
                'spawn_controllers': 'true',
            }.items(),
            condition=IfCondition(start_sim),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(mission_launch),
            condition=IfCondition(start_mission),
        ),
        Node(
            package='twist_mux',
            executable='twist_mux',
            name='twist_mux',
            output='screen',
            parameters=[twist_mux_params],
            remappings=[('cmd_vel_out', '/diff_drive_controller/cmd_vel')],
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav2_launch),
            launch_arguments={
                'use_sim_time': 'true',
                'map': map_file,
                'params_file': nav_params,
            }.items(),
        ),
    ]


def generate_launch_description():
    default_nav_params = PathJoinSubstitution(
        [FindPackageShare('sentinel_bringup'), 'config', 'nav2.yaml']
    )
    default_twist_mux_params = PathJoinSubstitution(
        [FindPackageShare('sentinel_bringup'), 'config', 'twist_mux.yaml']
    )
    default_map = PathJoinSubstitution(
        [FindPackageShare('sentinel_bringup'), 'maps', 'sentinel_phase7_demo.yaml']
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'start_sim',
                default_value='true',
                description='Start Gazebo simulation and controllers before navigation.',
            ),
            DeclareLaunchArgument(
                'headless',
                default_value='true',
                description='Run Gazebo in server-only mode.',
            ),
            DeclareLaunchArgument(
                'start_mission',
                default_value='true',
                description='Start Phase 6 mission manager with Nav2.',
            ),
            DeclareLaunchArgument(
                'map',
                default_value=default_map,
                description='Map YAML to load with Nav2.',
            ),
            DeclareLaunchArgument(
                'nav_params',
                default_value=default_nav_params,
                description='Nav2 parameter file.',
            ),
            DeclareLaunchArgument(
                'twist_mux_params',
                default_value=default_twist_mux_params,
                description='twist_mux parameter file.',
            ),
            OpaqueFunction(function=_launch_setup),
        ]
    )
