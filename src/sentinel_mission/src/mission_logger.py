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

"""Async mission event logger for mode and rosbag request topics."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import signal
from typing import Any

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import QoSProfile
from sentinel_interfaces.msg import RoverMode
from std_msgs.msg import Bool

try:
    from rclpy.experimental import AsyncNode
except ImportError:
    AsyncNode = Node


class MissionLogger(AsyncNode):
    """Record mission events without blocking subscription callbacks."""

    def __init__(self) -> None:
        super().__init__('mission_logger')
        self.declare_parameter('log_path', 'log/mission_events.jsonl')
        self._log_path = Path(str(self.get_parameter('log_path').value))
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.create_subscription(RoverMode, 'rover_mode', self._on_mode, QoSProfile(depth=10))
        self.create_subscription(
            Bool, 'record_request', self._on_record_request, QoSProfile(depth=10))
        self.create_subscription(
            Bool, 'stop_record_request', self._on_stop_record_request, QoSProfile(depth=10))

    def _on_mode(self, msg: RoverMode) -> None:
        self._queue.put_nowait({
            'event': 'mode',
            'mode': int(msg.mode),
            'mode_label': msg.mode_label,
            'stamp': {'sec': msg.stamp.sec, 'nanosec': msg.stamp.nanosec},
        })

    def _on_record_request(self, msg: Bool) -> None:
        if msg.data:
            self._queue.put_nowait({'event': 'record_request'})

    def _on_stop_record_request(self, msg: Bool) -> None:
        if msg.data:
            self._queue.put_nowait({'event': 'stop_record_request'})

    async def drain_events(self) -> None:
        """Drain queued events to a JSON lines file."""
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        while rclpy.ok():
            event = await self._queue.get()
            event['logger_time_ns'] = self.get_clock().now().nanoseconds
            with self._log_path.open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(event, sort_keys=True) + '\n')


async def async_main() -> None:
    """Run the async logger until ROS shuts down."""
    rclpy.init()
    node = MissionLogger()
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)
    try:
        log_task = asyncio.create_task(node.drain_events())
        spin_task = asyncio.create_task(spin_executor(executor))
        await stop_event.wait()
        log_task.cancel()
        spin_task.cancel()
    finally:
        executor.remove_node(node)
        node.destroy_node()
        rclpy.shutdown()


async def spin_executor(executor: SingleThreadedExecutor) -> None:
    """Spin ROS callbacks without blocking asyncio file writes."""
    while rclpy.ok():
        executor.spin_once(timeout_sec=0.1)
        await asyncio.sleep(0)


def main() -> None:
    """CLI entry point."""
    asyncio.run(async_main())


if __name__ == '__main__':
    main()
