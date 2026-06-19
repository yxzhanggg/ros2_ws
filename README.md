# Nexus Sentinel ROS 2 Workspace

Nexus Sentinel is a ROS 2 simulation workspace for a warehouse and campus inspection robot. The robot is intended to support autonomous patrol, mapping, operator teleoperation with a PS5 DualSense controller, and later safety/diagnostic workflows.

## Current Phase

Phase 6 is in progress: the workspace contains the control and DualSense teleoperation baselines plus a mission-management layer. The `mode_manager` lifecycle node publishes the current rover mode, accepts `/set_mode` requests, handles `/patrol_route` action goals in simulation mode, and `mission_logger` writes structured JSONL mission events.

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
│   ├── CHANGELOG.md
│   ├── DEPENDENCIES.md
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

Latest Phase 6 verification result: `sentinel_mission` and `sentinel_bringup` build and test cleanly. Runtime validation uses `ros2 launch sentinel_bringup mission.launch.py`, then checks `/mode_manager`, `/rover_mode`, `/set_mode`, `/patrol_route`, and `log/mission_events.jsonl`.

For phase-by-phase commands you can run yourself, see `docs/PHASE_TESTS.md`. It includes completed Phase 0-6 smoke tests and future Phase 7-10 acceptance-test templates.

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
