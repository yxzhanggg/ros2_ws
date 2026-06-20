# Nexus Sentinel ROS 2 Workspace

Nexus Sentinel is a ROS 2 simulation workspace for a warehouse and campus inspection robot. The robot is intended to support autonomous patrol, mapping, operator teleoperation with a PS5 DualSense controller, and later safety/diagnostic workflows.

## Current Phase

Phase 10 is complete: the workspace contains control, DualSense teleoperation, mission-management, navigation/mapping launch, composable perception, diagnostics, observability, integration-test, and documentation baselines. The project now includes `docs/ENGINEERING.md` for technical readers and `docs/LEARN_ROS2.md` for new ROS 2 learners.

## Workspace Layout

```text
ros2_ws/
├── src/
│   ├── sentinel_interfaces/
│   ├── sentinel_description/
│   ├── sentinel_gazebo/
│   ├── sentinel_control/
│   ├── sentinel_teleop/
│   ├── sentinel_mission/
│   ├── sentinel_perception/
│   └── sentinel_bringup/
├── docs/
│   ├── ACCEPTANCE.md
│   ├── CHANGELOG.md
│   ├── DEPENDENCIES.md
│   ├── ENGINEERING.md
│   ├── LEARN_ROS2.md
│   └── PHASE_TESTS.md
└── README.md
```

## Build And Test

On `nexus`:

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
colcon build
colcon test
colcon test-result --verbose
```

Latest Phase 10 verification result: documentation acceptance checks pass for README, `docs/ENGINEERING.md`, `docs/LEARN_ROS2.md`, `docs/DEPENDENCIES.md`, `docs/CHANGELOG.md`, and `docs/PHASE_TESTS.md`. The Phase 9 `sentinel_mission` tests remain green and provide the latest launch-testing runtime coverage.

For phase-by-phase commands you can run yourself, see `docs/PHASE_TESTS.md`. It includes completed Phase 0-10 smoke tests and documentation acceptance checks.

## Quick Start

On `nexus`:

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash

ros2 launch sentinel_gazebo sim.launch.py headless:=true spawn_controllers:=true
```

In another shell, try one focused subsystem:

```bash
ros2 launch sentinel_teleop gamepad.launch.py start_joy:=false
ros2 launch sentinel_bringup mission.launch.py
ros2 launch sentinel_perception perception.launch.py
ros2 launch sentinel_mission diagnostics.launch.py
```

## Simulation

Launch the headless Gazebo simulation on `nexus`:

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash
ros2 launch sentinel_gazebo sim.launch.py headless:=true
```

The Phase 3 launch starts Gazebo server mode, publishes `robot_description`, spawns `nexus_sentinel`, and bridges these sensor topics into ROS 2:

| Topic | Type | Source |
| --- | --- | --- |
| `/scan` | `sensor_msgs/msg/LaserScan` | Front 2D lidar |
| `/imu` | `sensor_msgs/msg/Imu` | Base IMU |
| `/camera/image` | `sensor_msgs/msg/Image` | Front camera |
| `/camera/camera_info` | `sensor_msgs/msg/CameraInfo` | Front camera info |
| `/clock` | `rosgraph_msgs/msg/Clock` | Gazebo simulation clock |

Phase 3 validation saw `/scan`, `/imu`, `/camera/image`, `/camera/camera_info`, `/joint_states`, `/tf`, and `/tf_static` in `ros2 topic list`.

## Control

Phase 4 adds controller configuration in `sentinel_control`:

| File | Purpose |
| --- | --- |
| `src/sentinel_control/config/controllers.yaml` | Controller manager, joint state, differential drive, and IMU broadcaster parameters |
| `src/sentinel_control/launch/control.launch.py` | Spawns the validated controllers against `/controller_manager` |

Use `spawn_controllers:=true` with the simulation launch:

```bash
ros2 launch sentinel_gazebo sim.launch.py headless:=true spawn_controllers:=true
```

Expected active controllers are `joint_state_broadcaster`, `diff_drive_controller`, and `imu_sensor_broadcaster`. In Lyrical, the differential-drive command and odometry topics are namespaced as `/diff_drive_controller/cmd_vel` and `/diff_drive_controller/odom`; the IMU broadcaster publishes `/imu_sensor_broadcaster/imu`, while the Gazebo bridge also publishes `/imu`.

## Teleoperation

Launch the simulation plus DualSense teleoperation pipeline:

```bash
ros2 launch sentinel_bringup teleop.launch.py
```

`joy_node` reads `/dev/input/js0` by default. `gamepad_interface` is a lifecycle node that publishes stamped velocity commands to `/diff_drive_controller/cmd_vel`; L1 is the deadman button, R2 scales speed, Square latches ESTOP, and R1 clears ESTOP. `twist_mux` is not installed on the current `nexus` image, so Phase 5 publishes directly to the controller while also publishing `/cmd_vel_lock` for the later mux integration.

For repeatable command-line validation without touching the controller:

```bash
ros2 launch sentinel_teleop gamepad.launch.py start_joy:=false
```

## Mission Management

Launch the mission baseline:

```bash
ros2 launch sentinel_bringup mission.launch.py
```

`mode_manager` is a C++ lifecycle node. It publishes `/rover_mode` with transient-local QoS, provides `/set_mode`, accepts mode requests from `/rover_mode_request`, and exposes the `/patrol_route` action. Because Nav2 is not installed on the current `nexus` image, Phase 6 patrol execution is a mission-manager simulation: it publishes PATROL feedback for each waypoint and returns to TELEOP when the route completes.

`mission_logger` is a Python node using Lyrical's available `rclpy.experimental.AsyncNode`. It records mode changes and record start/stop requests to `log/mission_events.jsonl`.

## Navigation And Mapping

Phase 7 adds launch and configuration assets for the intended SLAM/Nav2 stack:

| File | Purpose |
| --- | --- |
| `src/sentinel_bringup/launch/mapping.launch.py` | Starts simulation, teleop, `twist_mux`, and `slam_toolbox` when dependencies are installed |
| `src/sentinel_bringup/launch/nav.launch.py` | Starts simulation, mission manager, `twist_mux`, and Nav2 bringup when dependencies are installed |
| `src/sentinel_bringup/config/slam_toolbox.yaml` | Mapping parameters for `/scan`, `odom`, `map`, and `base_footprint` |
| `src/sentinel_bringup/config/nav2.yaml` | Nav2 AMCL, planner, controller, behavior, waypoint, map, and costmap parameters |
| `src/sentinel_bringup/config/twist_mux.yaml` | Teleop/Nav2 velocity arbitration and ESTOP lock configuration |
| `src/sentinel_bringup/maps/sentinel_phase7_demo.yaml` | Small demo map for launch wiring checks once Nav2 is present |
| `src/sentinel_bringup/routes/warehouse_loop.yaml` | Example warehouse patrol route |

On the current `nexus` image, these launches intentionally stop early and report the missing packages. After the dependencies are installed, rerun the commands in `docs/PHASE_TESTS.md` to validate real map publication, Nav2 action servers, and patrol execution.

## Perception

Launch the Phase 8 composable perception baseline:

```bash
ros2 launch sentinel_perception perception.launch.py
```

The launch starts `rclcpp_components`' `component_container_mt` with intra-process communication enabled for:

| Component | Input | Output | Role |
| --- | --- | --- | --- |
| `sentinel_perception::ScanFilterComponent` | `/scan` | `/scan_filtered` | Clamps invalid/out-of-range lidar ranges for later navigation/perception consumers |
| `sentinel_perception::ImageMarkerComponent` | `/camera/image` | `/detections` | Emits a lightweight JSON detection summary based on image brightness |

Phase 0 found no NVIDIA/CUDA stack on `nexus`, so Phase 8 documents GPU/rosidl buffer zero-copy as disabled and validates the CPU intra-process component path instead.

## Diagnostics And Observability

Launch mission diagnostics:

```bash
ros2 launch sentinel_mission diagnostics.launch.py
```

`health_monitor` uses `diagnostic_updater` to publish `/diagnostics` entries for:

| Diagnostic | Meaning |
| --- | --- |
| `health_monitor: battery` | Simulated battery percentage and drain rate |
| `health_monitor: controller` | Simulated controller heartbeat freshness |

`sentinel_mission` also has a `launch_testing` integration test that starts the mission stack, calls `/set_mode`, and waits for `/diagnostics`.

## Interfaces

`sentinel_interfaces` currently provides:

| Interface | Purpose |
| --- | --- |
| `sentinel_interfaces/msg/RoverMode` | Latched-style current mode state for TELEOP, MAPPING, PATROL, and ESTOP |
| `sentinel_interfaces/msg/Waypoint` | Named route waypoint with pose and dwell duration |
| `sentinel_interfaces/srv/SetMode` | Request/response API for mode changes |
| `sentinel_interfaces/action/PatrolRoute` | Patrol route action contract with progress feedback |

Inspect an interface on `nexus`:

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash
ros2 interface show sentinel_interfaces/action/PatrolRoute
```

## Documentation

| Document | Audience |
| --- | --- |
| `docs/ENGINEERING.md` | Engineering architecture, runtime graph, concept mapping, decisions, debugging, tests, and extension guide |
| `docs/LEARN_ROS2.md` | Chinese beginner tutorial using this project as the teaching example |
| `docs/PHASE_TESTS.md` | Copyable commands for each completed phase |
| `docs/ACCEPTANCE.md` | Final Phase 0-10 audit, acceptance matrix, and blocked runtime gates |
| `docs/DEPENDENCIES.md` | Real environment, installed/missing dependencies, and API differences |
| `docs/CHANGELOG.md` | Phase-by-phase implementation history |
