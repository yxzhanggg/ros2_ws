#!/usr/bin/env python3
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
"""Publish simulated robot health diagnostics for Nexus Sentinel."""

from __future__ import annotations

import math

from diagnostic_msgs.msg import DiagnosticStatus
import diagnostic_updater
import rclpy
from rclpy.node import Node


class HealthMonitor(Node):
    """Small diagnostic_updater based monitor for Phase 9 observability."""

    def __init__(self) -> None:
        super().__init__('health_monitor')
        self.declare_parameter('battery_start_percent', 96.0)
        self.declare_parameter('battery_warn_percent', 25.0)
        self.declare_parameter('battery_error_percent', 10.0)
        self.declare_parameter('battery_drain_percent_per_minute', 0.25)
        self.declare_parameter('controller_timeout_seconds', 2.0)
        self.declare_parameter('diagnostic_period', 1.0)

        self._battery_start_percent = float(
            self.get_parameter('battery_start_percent').value
        )
        self._battery_warn_percent = float(
            self.get_parameter('battery_warn_percent').value
        )
        self._battery_error_percent = float(
            self.get_parameter('battery_error_percent').value
        )
        self._battery_drain_percent_per_minute = float(
            self.get_parameter('battery_drain_percent_per_minute').value
        )
        self._controller_timeout_seconds = float(
            self.get_parameter('controller_timeout_seconds').value
        )
        diagnostic_period = float(self.get_parameter('diagnostic_period').value)

        self._started_time = self.get_clock().now()
        self._last_controller_update = self.get_clock().now()

        self._updater = diagnostic_updater.Updater(self, diagnostic_period)
        self._updater.setHardwareID('nexus_sentinel_sim')
        self._updater.add('battery', self._check_battery)
        self._updater.add('controller', self._check_controller)

        self.create_timer(0.5, self._tick)

    def _tick(self) -> None:
        self._last_controller_update = self.get_clock().now()
        self._updater.force_update()

    def _elapsed_minutes(self) -> float:
        elapsed = self.get_clock().now() - self._started_time
        return elapsed.nanoseconds / 1_000_000_000.0 / 60.0

    def _battery_percent(self) -> float:
        drain = self._elapsed_minutes() * self._battery_drain_percent_per_minute
        return max(0.0, self._battery_start_percent - drain)

    def _check_battery(self, stat):
        battery_percent = self._battery_percent()
        stat.add('battery_percent', f'{battery_percent:.2f}')
        stat.add('drain_percent_per_minute', f'{self._battery_drain_percent_per_minute:.2f}')

        if battery_percent <= self._battery_error_percent:
            stat.summary(DiagnosticStatus.ERROR, 'battery critically low')
        elif battery_percent <= self._battery_warn_percent:
            stat.summary(DiagnosticStatus.WARN, 'battery low')
        else:
            stat.summary(DiagnosticStatus.OK, 'battery nominal')
        return stat

    def _check_controller(self, stat):
        age = self.get_clock().now() - self._last_controller_update
        age_seconds = age.nanoseconds / 1_000_000_000.0
        healthy = math.isfinite(age_seconds) and age_seconds <= self._controller_timeout_seconds
        stat.add('last_update_age_seconds', f'{age_seconds:.3f}')
        stat.add('timeout_seconds', f'{self._controller_timeout_seconds:.2f}')
        if healthy:
            stat.summary(DiagnosticStatus.OK, 'controller heartbeat nominal')
        else:
            stat.summary(DiagnosticStatus.ERROR, 'controller heartbeat stale')
        return stat


def main(args=None) -> None:
    rclpy.init(args=args)
    node = HealthMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
