# Dependencies and Environment Baseline

This document records the real environment observed during Phase 0. It is intentionally factual: missing tools and blocked checks are listed as issues to resolve before later phases.

## Phase 0 Environment Baseline

Checked at: 2026-06-19T18:42:44+08:00, refreshed using ordinary `ssh nexus` as requested.

### Host

| Item | Observed value |
| --- | --- |
| Target host | `nexus` |
| OS | Ubuntu 26.04 LTS (`resolute`) |
| Kernel | `Linux nexus 7.0.0-22-generic #22-Ubuntu SMP PREEMPT_DYNAMIC Mon May 25 15:54:34 UTC 2026 x86_64 GNU/Linux` |
| Workspace | `/home/zyx/ros2_ws` |
| Workspace state | Git repository on branch `main`; currently contains Phase 0 docs and `.gitignore` |
| Git | `git version 2.53.0`; global user `yxzhanggg <yxzhanggg@gmail.com>` |

### ROS 2

| Item | Observed value |
| --- | --- |
| ROS installation | `/opt/ros/lyrical` exists |
| Non-interactive shell | `ROS_DISTRO` and `ros2` are not available until `/opt/ros/lyrical/setup.bash` is sourced |
| After setup | `ROS_DISTRO=lyrical`; `ros2 --help` works |
| Installed ROS base package | `ros-lyrical-ros-base 0.13.0-3resolute.20260606.042427` |
| Installed ROS CLI package | `ros-lyrical-ros2cli 0.40.7-1resolute.20260606.033717` |
| RMW observed by `ros2 doctor --report` | `rmw_fastrtps_cpp` |
| Discovery range | `ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET` |

Command pattern required for later phases:

```bash
source /opt/ros/lyrical/setup.bash
```

### Build Tooling

| Tool | Observed value |
| --- | --- |
| `colcon` | `/usr/bin/colcon` |
| Installed package | `colcon 0.20.0-1` plus related `python3-colcon-*` packages |
| Phase 0 build check | `colcon build` completed in the empty workspace with no packages to build |
| Phase 0 test check | `colcon test` completed in the empty workspace with no packages to test |
| C++ compiler | `/usr/bin/c++` and `/usr/bin/g++`, GCC 15.2.0, installed by the operator before Phase 1 continued |
| Phase 1 build check | `colcon build --event-handlers console_direct+` completed: 8 packages finished |
| Phase 1 test check | `colcon test --event-handlers console_direct+` and `colcon test-result --verbose` completed: 40 tests, 0 errors, 0 failures, 1 skipped |
| Phase 2 interface check | `ros2 interface show` succeeded for `RoverMode`, `Waypoint`, `SetMode`, and `PatrolRoute` |
| Phase 2 build/test check | `colcon build` and `colcon test` completed: 8 packages, 40 tests, 0 errors, 0 failures, 1 skipped |
| Phase 3 description check | `xacro` plus `check_urdf` succeeded for `sentinel_description/urdf/sentinel.urdf.xacro` |
| Phase 3 simulation package check | `colcon build --packages-select sentinel_description sentinel_gazebo` and matching `colcon test` completed: 46 tests, 0 errors, 0 failures, 1 skipped |

### Gazebo / gz

| Item | Observed value |
| --- | --- |
| `gz` executable | `/opt/ros/lyrical/opt/gz_tools_vendor/bin/gz` after sourcing `/opt/ros/lyrical/setup.bash` |
| `gz sim --version` | `10.1.1` |
| Installed gz-related packages | Full ROS gz vendor stack is present, including `ros-lyrical-gz-sim-vendor`, `ros-lyrical-gz-tools-vendor`, `ros-lyrical-ros-gz`, `ros-lyrical-ros-gz-sim`, and `ros-lyrical-gz-ros2-control` |
| Phase 3 launch result | `ros2 launch sentinel_gazebo sim.launch.py headless:=true` started Gazebo server mode, initialized `robot_state_publisher`, spawned `nexus_sentinel`, and created bridges for `/clock`, `/scan`, `/imu`, `/camera/image`, and `/camera/camera_info` |
| Result | Gazebo is available after sourcing the ROS environment; Phase 3 simulation launch is functional in headless SSH mode |

Phase 3 observed ROS topics during a clean headless simulation launch:

```text
/camera/camera_info
/camera/image
/clock
/imu
/joint_states
/parameter_events
/robot_description
/rosout
/scan
/tf
/tf_static
```

### URDF 1.2 Compatibility Check

Phase 3 checked the installed Lyrical files under `/opt/ros/lyrical` for the requested URDF 1.2 features. No confirmed parser support for `quat_xyzw` joint origins or `capsule` collision geometry was found in the installed headers/share files. To keep the Definition of Done runnable, the robot description uses standard URDF `rpy` origins and primitive box/cylinder/sphere fallback collision geometry. The current sensor mounts are zero-rotation joints, equivalent to `quat_xyzw="0 0 0 1"` semantically, but the file does not emit unsupported XML attributes.

### ros_gz_bridge Launch Compatibility

The installed `ros_gz_bridge` package provides `ros_gz_bridge.launch.py`, but including it failed in this environment because its `RosGzBridge` action expected `bridge_params` as a list while the launch file passed a `LaunchConfiguration`. Phase 3 therefore starts `ros_gz_bridge`'s `parameter_bridge` executable directly and passes the validated `config_file` parameter.

### Controller / DualSense

| Item | Observed value |
| --- | --- |
| Bluetooth device | `AC:36:1B:17:37:A3 DualSense Wireless Controller` |
| Pairing state | Paired: yes; Bonded: yes; Trusted: yes; Blocked: no; Connected: yes |
| Joystick devices | `/dev/input/js0`, `/dev/input/js1` |
| `/dev/input/js0` | `DualSense Wireless Controller`, 8 axes and 13 buttons via `jstest --normal` |
| `/dev/input/js1` | `DualSense Wireless Controller Motion Sensors`, 6 axes and 0 buttons via `jstest --normal` |
| `/dev/input/by-id` | Not present during the check |
| `jstest` / `evtest` | `/usr/bin/jstest`, `/usr/bin/evtest` |
| Installed ROS joystick package | `ros-lyrical-joy 3.3.0-4resolute.20260606.031052` is installed |
| Additional teleop package | `ros-lyrical-teleop-twist-joy 2.6.5-3resolute.20260606.031807` is installed, but the project will still implement its own `gamepad_interface` node as required |

DualSense default axis/button snapshot from `/dev/input/js0`:

```text
Joystick (DualSense Wireless Controller) has 8 axes (X, Y, Z, Rx, Ry, Rz, Hat0X, Hat0Y)
and 13 buttons (BtnA, BtnB, BtnX, BtnY, BtnTL, BtnTR, BtnTL2, BtnTR2, BtnSelect, BtnStart, BtnMode, BtnThumbL, BtnThumbR).
```

Motion sensor snapshot from `/dev/input/js1`:

```text
Joystick (DualSense Wireless Controller Motion Sensors) has 6 axes (X, Y, Z, Rx, Ry, Rz)
and 0 buttons ().
```

### GPU and Display

| Item | Observed value |
| --- | --- |
| GPU | Intel TigerLake-LP GT2 Iris Xe Graphics |
| NVIDIA GPU | `nvidia-smi` not found |
| Login session | Wayland session detected (`Type=wayland`, `Remote=no`) |
| SSH non-interactive `DISPLAY` | Empty |
| Visualization choice | Prefer documented headless/server workflow for SSH. Local desktop GUI may be possible from the active Wayland session, but Phase 0 SSH shell has no display environment. |
| Optional GPU zero-copy demo | No NVIDIA/CUDA path detected. Later zero-copy/GPU demo should default to CPU path unless a supported GPU stack is explicitly added. |

### Network and SSH Notes

The Codex app is running on macOS, but the target ROS machine is reachable with the configured command:

```bash
ssh nexus hostname
```

Ordinary `ssh nexus` succeeded during the Phase 0 refresh and should be used by default. A few rapid concurrent SSH commands still showed transient local `nexus.local` resolution failures; retrying the same `ssh nexus` command succeeded.

## Missing Dependencies Identified in Phase 0

These items are required for later phases but were not installed or not usable during Phase 0:

| Dependency | Why it is needed | Phase affected |
| --- | --- | --- |
| Nav2, slam_toolbox, twist_mux, controllers, and any remaining navigation packages | Required by architecture and later phases; package availability still needs complete verification before Phase 3+ | Phase 3 onward |

No network downloads, package installs, `sudo`, system service changes, udev rules, or user group changes were executed by Codex during this Phase 0 refresh. A later source refresh showed that the vendored Gazebo stack is already available through `/opt/ros/lyrical/setup.bash`.

## Phase 1 Package Baseline

| Package | Build type | Phase 1 role |
| --- | --- | --- |
| `sentinel_interfaces` | `ament_cmake` | Placeholder for custom messages, services, and actions to be implemented in Phase 2 |
| `sentinel_description` | `ament_cmake` | Placeholder for Xacro, meshes, and RViz assets to be implemented in Phase 3 |
| `sentinel_gazebo` | `ament_cmake` | Placeholder for Gazebo worlds, models, and launch files to be implemented in Phase 3 |
| `sentinel_control` | `ament_cmake` | Placeholder for ros2_control YAML and controller launch assets to be implemented in Phase 4 |
| `sentinel_teleop` | `ament_python` | Placeholder for DualSense teleoperation nodes and parameters to be implemented in Phase 5 |
| `sentinel_mission` | `ament_cmake` | Placeholder for C++ mission management and later Python logging integration |
| `sentinel_perception` | `ament_cmake` | Placeholder for composable C++ perception nodes to be implemented in Phase 8 |
| `sentinel_bringup` | `ament_cmake` | Placeholder for top-level launch, parameters, and RViz configuration |

Phase 1 keeps CMake package configuration intentionally lightweight so empty skeleton packages build before later-phase runtime dependencies are fully exercised. Declared dependencies in `package.xml` preserve the intended architecture.

## Phase 2 Interface Baseline

| Interface | Fields / role |
| --- | --- |
| `sentinel_interfaces/msg/RoverMode` | `MODE_TELEOP`, `MODE_MAPPING`, `MODE_PATROL`, `MODE_ESTOP`, `mode`, `mode_label`, `stamp` |
| `sentinel_interfaces/msg/Waypoint` | `name`, `geometry_msgs/Pose pose`, `dwell_seconds` |
| `sentinel_interfaces/srv/SetMode` | Request: `mode`; response: `success`, `message`, `RoverMode current_mode` |
| `sentinel_interfaces/action/PatrolRoute` | Goal: waypoints and loop flag; result: success/count/message; feedback: current waypoint, remaining distance, estimated remaining time |

The interface package uses `rosidl_default_generators` and exports `rosidl_default_runtime`. Lyrical generated C, C++, Python, and Rust artifacts during the Phase 2 build.

## Phase 3 Simulation Baseline

| Asset | Location | Role |
| --- | --- | --- |
| Xacro model | `src/sentinel_description/urdf/sentinel.urdf.xacro` | Differential-drive base, wheels, casters, sensor mounts, sensor plugins, and `gz_ros2_control` declaration |
| Description launch | `src/sentinel_description/launch/description.launch.py` | Publishes `robot_description` through `robot_state_publisher` |
| Gazebo world | `src/sentinel_gazebo/worlds/sentinel_warehouse.sdf` | Headless warehouse/campus world with walls, racks, dock, and obstacle geometry |
| Simulation launch | `src/sentinel_gazebo/launch/sim.launch.py` | Starts Gazebo server mode, publishes robot state, spawns `nexus_sentinel`, and starts topic bridging |
| Bridge config | `src/sentinel_gazebo/config/bridge.yaml` | Bridges `/clock`, `/scan`, `/imu`, `/camera/image`, and `/camera/camera_info` from Gazebo to ROS 2 |

Run Phase 3 simulation on `nexus`:

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash
ros2 launch sentinel_gazebo sim.launch.py headless:=true
```
