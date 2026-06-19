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
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    perception_config = LaunchConfiguration('perception_config')

    default_config = PathJoinSubstitution(
        [FindPackageShare('sentinel_perception'), 'config', 'perception.yaml']
    )

    container = ComposableNodeContainer(
        name='sentinel_perception_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container_mt',
        output='screen',
        composable_node_descriptions=[
            ComposableNode(
                package='sentinel_perception',
                plugin='sentinel_perception::ScanFilterComponent',
                name='scan_filter',
                parameters=[perception_config],
                remappings=[
                    ('scan', '/scan'),
                    ('scan_filtered', '/scan_filtered'),
                ],
                extra_arguments=[{'use_intra_process_comms': True}],
            ),
            ComposableNode(
                package='sentinel_perception',
                plugin='sentinel_perception::ImageMarkerComponent',
                name='image_marker_detector',
                parameters=[perception_config],
                remappings=[
                    ('camera/image', '/camera/image'),
                    ('detections', '/detections'),
                ],
                extra_arguments=[{'use_intra_process_comms': True}],
            ),
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'perception_config',
                default_value=default_config,
                description='Perception component parameter file.',
            ),
            container,
        ]
    )
