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

    required_packages = ['slam_toolbox', 'twist_mux']
    missing = _missing_packages(required_packages)
    if missing:
        return [
            LogInfo(
                msg=[
                    'Phase 7 mapping dependencies are missing: ',
                    ', '.join(missing),
                    '. Install the matching ROS Lyrical packages, then rerun this launch.',
                ]
            ),
            EmitEvent(event=Shutdown(reason='missing Phase 7 mapping dependencies')),
        ]

    headless = LaunchConfiguration('headless')
    start_sim = LaunchConfiguration('start_sim')
    start_joy = LaunchConfiguration('start_joy')
    slam_params = LaunchConfiguration('slam_params')
    twist_mux_params = LaunchConfiguration('twist_mux_params')

    sim_launch = PathJoinSubstitution(
        [FindPackageShare('sentinel_gazebo'), 'launch', 'sim.launch.py']
    )
    gamepad_launch = PathJoinSubstitution(
        [FindPackageShare('sentinel_teleop'), 'launch', 'gamepad.launch.py']
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
            PythonLaunchDescriptionSource(gamepad_launch),
            launch_arguments={
                'cmd_vel_topic': '/cmd_vel_teleop',
                'start_joy': start_joy,
            }.items(),
        ),
        Node(
            package='twist_mux',
            executable='twist_mux',
            name='twist_mux',
            output='screen',
            parameters=[twist_mux_params],
            remappings=[('cmd_vel_out', '/diff_drive_controller/cmd_vel')],
        ),
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[slam_params],
        ),
    ]


def generate_launch_description():
    default_slam_params = PathJoinSubstitution(
        [FindPackageShare('sentinel_bringup'), 'config', 'slam_toolbox.yaml']
    )
    default_twist_mux_params = PathJoinSubstitution(
        [FindPackageShare('sentinel_bringup'), 'config', 'twist_mux.yaml']
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'start_sim',
                default_value='true',
                description='Start Gazebo simulation and controllers before mapping.',
            ),
            DeclareLaunchArgument(
                'headless',
                default_value='true',
                description='Run Gazebo in server-only mode.',
            ),
            DeclareLaunchArgument(
                'start_joy',
                default_value='true',
                description='Start joy_node for DualSense manual mapping.',
            ),
            DeclareLaunchArgument(
                'slam_params',
                default_value=default_slam_params,
                description='slam_toolbox parameter file.',
            ),
            DeclareLaunchArgument(
                'twist_mux_params',
                default_value=default_twist_mux_params,
                description='twist_mux parameter file.',
            ),
            OpaqueFunction(function=_launch_setup),
        ]
    )
