# Final Acceptance Audit

Checked on: 2026-06-20

Scope: Nexus Sentinel Phase 0-10 baseline on `nexus:/home/zyx/ros2_ws`.

This document records what has been verified on the actual `nexus` host and what remains blocked by missing runtime dependencies. It is intentionally conservative: passing items are backed by commands, and blocked items are not counted as complete runtime behavior.

## Audit Commands

Run on `nexus`:

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash

colcon build --event-handlers console_direct+
colcon test --event-handlers console_direct+
colcon test-result --verbose
```

Observed result:

```text
Summary: 8 packages finished
Summary: 116 tests, 0 errors, 0 failures, 8 skipped
```

Repository and macOS metadata checks:

```bash
cd ~/ros2_ws
git status --short
find . -name .DS_Store -print
```

Observed result: clean remote worktree after commit; no `.DS_Store` files on the remote workspace.

Dependency check:

```bash
source /opt/ros/lyrical/setup.bash
ros2 pkg list | grep -E '^(controller_manager|ros2controlcli|joint_state_broadcaster|diff_drive_controller|imu_sensor_broadcaster|twist_mux|slam_toolbox|nav2_msgs|nav2_bringup|diagnostic_updater|joy|rclcpp_components)$' | sort
```

Observed installed packages:

```text
controller_manager
diagnostic_updater
diff_drive_controller
imu_sensor_broadcaster
joint_state_broadcaster
joy
rclcpp_components
ros2controlcli
```

Observed missing ROS packages relevant to the full product story:

```text
twist_mux
slam_toolbox
nav2_msgs
nav2_bringup
```

## Acceptance Matrix

| Requirement | Status | Evidence |
| --- | --- | --- |
| Phase 0-10 have been executed in order | Pass | Git history contains Phase 0-10 commits; README and changelog document each phase |
| All eight `sentinel_*` packages exist | Pass | `sentinel_interfaces`, `sentinel_description`, `sentinel_gazebo`, `sentinel_control`, `sentinel_teleop`, `sentinel_mission`, `sentinel_perception`, `sentinel_bringup` |
| Full workspace build and test are green | Pass | `8 packages finished`; `116 tests, 0 errors, 0 failures, 8 skipped` |
| Custom msg/srv/action interfaces exist | Pass | `RoverMode`, `Waypoint`, `SetMode`, `PatrolRoute` |
| Gazebo simulation baseline starts headless | Pass | Phase 3 smoke test spawned `nexus_sentinel` and exposed sensor topics |
| ros2_control differential-drive stack is wired | Pass | Controller packages now present; Phase 4 validation recorded active controllers, odom, TF, and command response |
| DualSense teleop pipeline exists | Pass | `joy_node`, `gamepad_interface` lifecycle node, `/cmd_vel_lock`, mode request topics, typed parameters, and unit tests |
| Deadman/ESTOP behavior is testable | Pass | Synthetic `/joy` tests verify nonzero command with L1, zero command after release, Square ESTOP lock |
| Physical hand-controller driving is ready for operator test | Operator-test required | The runnable manual command is documented in `docs/PHASE_TESTS.md`; Codex cannot physically hold the controller in this final audit |
| Mode manager, service, action, and logging exist | Pass | `/set_mode`, `/rover_mode`, `/patrol_route`, `mission_events.jsonl`; launch test covers mode change and diagnostics |
| Full Nav2 autonomous patrol loop | Blocked | `nav2_bringup`, `nav2_msgs`, `slam_toolbox`, and `twist_mux` are missing on this host |
| Mapping launch and Nav2 launch assets exist | Pass as config baseline | `mapping.launch.py`, `nav.launch.py`, SLAM/Nav2/twist_mux YAML, demo map, route YAML |
| Hand-over from autonomous patrol to teleop and back | Blocked | Requires real Nav2/twist_mux runtime stack |
| ESTOP through final twist arbitration | Partial | `gamepad_interface` publishes `/cmd_vel_lock`; final mux lock behavior waits for `twist_mux` install/type verification |
| Composable perception container | Pass | `ScanFilterComponent` and `ImageMarkerComponent` in an intra-process component container |
| Diagnostics and observability | Pass | `health_monitor` publishes `/diagnostics`; launch test and CLI examples are documented |
| rosbag2 remote service control | Partial | Create/Options publish record request topics; service-level rosbag2 remote-control wiring is deferred |
| Documentation deliverables | Pass | `README.md`, `docs/ENGINEERING.md`, `docs/LEARN_ROS2.md`, `docs/DEPENDENCIES.md`, `docs/CHANGELOG.md`, `docs/PHASE_TESTS.md` |
| macOS `.DS_Store` not copied/staged | Pass | Remote `find . -name .DS_Store -print` had no output; local `.DS_Store` was not staged |
| No unapproved `sudo` or system-level edits by Codex | Pass | System package changes were requested from the operator when needed; final audit used only project files and read-only package checks |

## Current Operator-Ready Tests

These are the most useful commands for trying the completed baseline:

```bash
ssh nexus
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash

ros2 launch sentinel_gazebo sim.launch.py headless:=true spawn_controllers:=true
```

In a second shell:

```bash
ssh nexus
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash

ros2 launch sentinel_bringup teleop.launch.py
```

For command-line checks that do not require physically using the controller:

```bash
ros2 launch sentinel_teleop gamepad.launch.py start_joy:=false
ros2 launch sentinel_bringup mission.launch.py
ros2 launch sentinel_perception perception.launch.py
ros2 launch sentinel_mission diagnostics.launch.py
```

The full phase-by-phase playbook remains in `docs/PHASE_TESTS.md`.

## Next Gate Before Claiming Full Product Acceptance

Do not mark the complete product story as fully accepted until these dependencies are installed or otherwise provided with explicit approval:

```text
twist_mux
slam_toolbox
nav2_msgs
nav2_bringup
```

After that, rerun the Phase 7 full runtime tests in `docs/PHASE_TESTS.md`, then verify:

- Mapping publishes `/map`.
- Nav2 action servers are available.
- `PatrolRoute` internally delegates to Nav2 instead of simulation-mode waypoint timing.
- `twist_mux` arbitrates teleop over Nav2 and honors `/cmd_vel_lock`.
- The robot can complete the intended mapping -> patrol -> teleop takeover -> resume workflow in simulation.
