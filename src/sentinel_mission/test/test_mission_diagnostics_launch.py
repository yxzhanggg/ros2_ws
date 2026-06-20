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

import time
import unittest

from diagnostic_msgs.msg import DiagnosticArray
import launch
import launch.actions
import launch.launch_description_sources
import launch.substitutions
import launch_ros.actions
import launch_ros.substitutions
import launch_testing.actions
import launch_testing.markers
from launch_testing_ros.actions import EnableRmwIsolation

import pytest
import rclpy
from sentinel_interfaces.srv import SetMode


@pytest.mark.launch_test
@launch_testing.markers.keep_alive
def generate_test_description():
    mission_launch = launch.substitutions.PathJoinSubstitution(
        [
            launch_ros.substitutions.FindPackageShare('sentinel_mission'),
            'launch',
            'mission.launch.py',
        ]
    )

    return launch.LaunchDescription(
        [
            EnableRmwIsolation(),
            launch.actions.IncludeLaunchDescription(
                launch.launch_description_sources.PythonLaunchDescriptionSource(
                    mission_launch
                ),
                launch_arguments={
                    'log_path': '/tmp/sentinel_launch_test_events.jsonl',
                    'start_health_monitor': 'true',
                }.items(),
            ),
            launch_testing.actions.ReadyToTest(),
        ]
    )


class TestMissionDiagnostics(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.shutdown()

    def setUp(self):
        self.node = rclpy.create_node('mission_diagnostics_launch_test')

    def tearDown(self):
        self.node.destroy_node()

    def test_set_mode_service_and_diagnostics(self):
        client = self.node.create_client(SetMode, '/set_mode')
        deadline = time.time() + 8.0
        while not client.wait_for_service(timeout_sec=0.2):
            if time.time() > deadline:
                self.fail('/set_mode service did not become available')

        request = SetMode.Request()
        request.mode = 1
        future = client.call_async(request)
        rclpy.spin_until_future_complete(self.node, future, timeout_sec=5.0)
        self.assertTrue(future.done())
        response = future.result()
        self.assertTrue(response.success)
        self.assertEqual(response.current_mode.mode_label, 'MAPPING')

        diagnostics = []
        sub = self.node.create_subscription(
            DiagnosticArray,
            '/diagnostics',
            lambda msg: diagnostics.append(msg),
            10,
        )
        deadline = time.time() + 8.0
        while not diagnostics and time.time() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.2)
        self.node.destroy_subscription(sub)

        self.assertTrue(diagnostics)
        names = {status.name for status in diagnostics[-1].status}
        self.assertTrue(any('battery' in name for name in names), names)
        self.assertTrue(any('controller' in name for name in names), names)
