# Nexus Sentinel ROS 2 Workspace

Nexus Sentinel is a ROS 2 simulation workspace for a warehouse and campus inspection robot. The robot is intended to support autonomous patrol, mapping, operator teleoperation with a PS5 DualSense controller, and later safety/diagnostic workflows.

## Current Phase

Phase 3 is complete: the workspace contains the package skeletons, custom ROS 2 interfaces, a parameterized Nexus Sentinel Xacro model, and a headless Gazebo warehouse simulation with lidar, IMU, and camera topic bridges. Controllers, teleoperation, mission logic, navigation, perception, and expanded documentation will be implemented in later phases.

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
│   └── DEPENDENCIES.md
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

Latest Phase 3 verification result: all 8 packages built successfully; 46 tests ran with 0 errors, 0 failures, and 1 skipped template copyright test.

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
