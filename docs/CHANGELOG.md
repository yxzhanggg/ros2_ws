# Changelog

## 2026-06-20 - Final Acceptance Audit

### Added

- Added `docs/ACCEPTANCE.md` with the Phase 0-10 acceptance matrix, final audit commands, current runtime dependency gates, and operator-ready smoke tests.

### Changed

- Updated README, `docs/DEPENDENCIES.md`, and `docs/PHASE_TESTS.md` to link the final acceptance audit.

### Verified

- Ran a full workspace build and test on `nexus`: 8 packages finished; 116 tests, 0 errors, 0 failures, 8 skipped.
- Confirmed the remote workspace had no `.DS_Store` files.
- Confirmed `controller_manager`, `ros2controlcli`, `joint_state_broadcaster`, `diff_drive_controller`, `imu_sensor_broadcaster`, `joy`, `diagnostic_updater`, and `rclcpp_components` are installed.
- Confirmed `twist_mux`, `slam_toolbox`, `nav2_msgs`, and `nav2_bringup` are still missing, so the final Nav2/SLAM patrol loop remains a documented dependency gate.

## 2026-06-20 - Phase 10 Documentation Baseline

### Added

- Added `docs/ENGINEERING.md`, a Chinese engineering document covering architecture, package roles, runtime graph, ROS 2 concept mapping, design decisions, API differences, build/run/debug commands, testing strategy, and extension guidance.
- Added `docs/LEARN_ROS2.md`, a Chinese beginner tutorial that teaches ROS 2 concepts through the actual Nexus Sentinel files and commands, with self-check questions.

### Changed

- Updated README with Phase 10 status, quick start commands, and a documentation index.
- Updated `docs/PHASE_TESTS.md` with concrete Phase 10 documentation acceptance commands.
- Updated `docs/DEPENDENCIES.md` with the Phase 10 documentation verification record.

### Verified

- Documentation acceptance checks passed for README, `docs/ENGINEERING.md`, `docs/LEARN_ROS2.md`, `docs/DEPENDENCIES.md`, `docs/CHANGELOG.md`, and `docs/PHASE_TESTS.md`.
- Phase 9 runtime coverage remains represented by the green `sentinel_mission` launch test: 116 tests, 0 errors, 0 failures, 8 skipped.

## 2026-06-20 - Phase 9 Diagnostics and Observability Baseline

### Added

- Added `sentinel_mission.health_monitor`, a Python `diagnostic_updater` node that publishes battery and controller health on `/diagnostics`.
- Added `sentinel_mission/launch/diagnostics.launch.py` for standalone diagnostic validation.
- Extended `sentinel_mission/launch/mission.launch.py` with an optional `start_health_monitor` argument.
- Added a `launch_testing` integration test that launches the mission stack, calls `/set_mode`, and verifies `/diagnostics` contains battery and controller statuses.

### Changed

- Updated README, `docs/PHASE_TESTS.md`, and `docs/DEPENDENCIES.md` with Phase 9 diagnostic, launch test, and observability commands.
- Recorded actual examples for `ros2 doctor --report`, `ros2 topic bw /diagnostics`, and `ros2 service info /set_mode --verbose`.

### Verified

- `colcon build --packages-select sentinel_mission --event-handlers console_direct+` passed.
- `colcon test --packages-select sentinel_mission --event-handlers console_direct+` plus `colcon test-result --verbose` passed: 116 tests, 0 errors, 0 failures, 8 skipped.
- `ros2 launch sentinel_mission diagnostics.launch.py` published `/diagnostics` with `health_monitor: battery` and `health_monitor: controller`.
- The launch test switched the mode manager to `MAPPING` via `/set_mode` and observed diagnostic output.
- `ros2 topic bw /diagnostics` reported about `1.15-1.46 KB/s` with diagnostic messages around `0.35 KB`.

## 2026-06-20 - Phase 8 Composable Perception Baseline

### Added

- Added `sentinel_perception::ScanFilterComponent`, a C++ composable node that subscribes to `/scan` with SensorDataQoS and publishes `/scan_filtered`.
- Added `sentinel_perception::ImageMarkerComponent`, a C++ composable node that subscribes to `/camera/image` and publishes lightweight JSON detection summaries on `/detections`.
- Added `sentinel_perception/launch/perception.launch.py` using `rclcpp_components` `component_container_mt` with intra-process communication enabled for both components.
- Added `sentinel_perception/config/perception.yaml` with typed parameters for lidar filtering and image brightness detection.

### Changed

- Updated `sentinel_perception` CMake/package metadata to build and register the component library.
- Updated README, `docs/PHASE_TESTS.md`, and `docs/DEPENDENCIES.md` with Phase 8 commands, test outputs, and GPU/zero-copy notes.

### Verified

- `colcon build --packages-select sentinel_perception --event-handlers console_direct+` passed.
- `colcon test --packages-select sentinel_perception --event-handlers console_direct+` plus `colcon test-result --verbose` passed: 108 tests, 0 errors, 0 failures, 8 skipped.
- `ros2 launch sentinel_perception perception.launch.py` loaded `/scan_filter` and `/image_marker_detector` into `/sentinel_perception_container`.
- Synthetic `/scan` input produced `/scan_filtered` with invalid/out-of-range values clamped to `12.0`.
- Synthetic mono8 `/camera/image` input produced `/detections` JSON with `mean_brightness: 255.00` and `bright_marker: true`.

### Notes

- No NVIDIA/CUDA path was detected in Phase 0, so Phase 8 validates CPU intra-process component communication and leaves GPU/rosidl buffer zero-copy disabled for this machine.

## 2026-06-20 - Phase 7 Navigation and Mapping Baseline

### Added

- Added `sentinel_bringup/launch/mapping.launch.py` for the intended simulation, teleop, `twist_mux`, and `slam_toolbox` mapping stack.
- Added `sentinel_bringup/launch/nav.launch.py` for the intended simulation, mission manager, `twist_mux`, and Nav2 bringup stack.
- Added SLAM, Nav2, and twist mux parameter files under `sentinel_bringup/config/`.
- Added a small demo occupancy map and an example `warehouse_loop` patrol route under `sentinel_bringup/maps/` and `sentinel_bringup/routes/`.
- Updated `sentinel_bringup` installation rules so config, launch, maps, routes, resource, and RViz directories are installed together.

### Changed

- Updated README, `docs/PHASE_TESTS.md`, and `docs/DEPENDENCIES.md` with Phase 7 commands and dependency findings.
- Added explicit launch-time dependency checks so Phase 7 mapping/navigation launches report missing packages cleanly on the current `nexus` image.

### Verified

- `colcon build --packages-select sentinel_bringup --event-handlers console_direct+` passed.
- `colcon test --packages-select sentinel_bringup --event-handlers console_direct+` plus `colcon test-result --verbose` passed: 84 tests, 0 errors, 0 failures, 4 skipped.
- `ros2 launch sentinel_bringup mapping.launch.py start_sim:=false start_joy:=false` reported missing `slam_toolbox` and `twist_mux`.
- `ros2 launch sentinel_bringup nav.launch.py start_sim:=false start_mission:=false` reported missing `nav2_bringup`, `nav2_msgs`, and `twist_mux`.

### Blocked

- Full Phase 7 DoD is blocked because `slam_toolbox`, `nav2_bringup`, and `nav2_msgs` are not installed and were not found as normal ROS Lyrical apt packages in the current index. `twist_mux` is available from apt but not installed.
- The `twist_mux` velocity message type and final remapping must be verified after installation because the current teleop/control path uses `geometry_msgs/msg/TwistStamped`.

## 2026-06-20 - Phase 6 Mission Management Baseline

### Added

- Added `sentinel_mission::ModeManager`, a C++ lifecycle node that publishes `/rover_mode` with transient-local QoS.
- Added `/set_mode` service handling and `/rover_mode_request` subscription so Phase 5 teleop mode requests can update the shared mode state.
- Added `/patrol_route` action server for `sentinel_interfaces/action/PatrolRoute`.
- Added `mission_logger`, a Python logger node that writes `/rover_mode`, `/record_request`, and `/stop_record_request` events to JSONL.
- Added `sentinel_mission/launch/mission.launch.py` and `sentinel_bringup/launch/mission.launch.py`.

### Changed

- Updated README, `docs/PHASE_TESTS.md`, and `docs/DEPENDENCIES.md` with Phase 6 launch, test, runtime, and Lyrical API notes.
- Documented that Nav2 packages are not installed on the current `nexus` image, so Phase 6 patrol execution uses a mission-manager simulation loop and the real Nav2 handoff is deferred to Phase 7.

### Verified

- `colcon build --packages-select sentinel_mission sentinel_bringup --event-handlers console_direct+` passed.
- `colcon test --packages-select sentinel_mission sentinel_bringup --event-handlers console_direct+` plus `colcon test-result --verbose` passed: 75 tests, 0 errors, 0 failures, 4 skipped.
- `ros2 launch sentinel_bringup mission.launch.py` brought `/mode_manager` to lifecycle state `active`.
- `/rover_mode` published the current mode with transient-local behavior; a late `ros2 topic echo /rover_mode --once` received the current state.
- `/set_mode` accepted `mode: 1` and published `MAPPING`.
- `/patrol_route` accepted a one-waypoint route, published feedback for `dock`, and returned `SUCCEEDED` with `waypoints_completed: 1`.
- `log/mission_events.jsonl` recorded `MAPPING -> PATROL -> TELEOP`.

## 2026-06-19 - Phase 5 DualSense Teleoperation Baseline

### Added

- Added `sentinel_teleop.gamepad_interface`, a Python lifecycle node that maps DualSense `/joy` input to stamped velocity commands, mode-request messages, record-request topics, and an ESTOP lock topic.
- Added `sentinel_teleop/config/gamepad.yaml` with typed YAML parameters for DualSense axis/button mapping, deadzone, speed limits, and frame id.
- Added `sentinel_teleop/launch/gamepad.launch.py` for `joy_node` plus automatic lifecycle configure/activate of `gamepad_interface`.
- Added `sentinel_bringup/launch/teleop.launch.py` to start the Phase 4 simulation/controllers and the Phase 5 teleop pipeline together.
- Added unit tests for deadman behavior, trigger speed scaling, ESTOP latch/clear, mode buttons, and record request detection.

### Changed

- Updated README and `docs/PHASE_TESTS.md` with Phase 5 launch and validation commands.
- Recorded that `ros-lyrical-twist-mux` is available in apt but not installed, so the current Phase 5 runtime remaps teleop directly to `/diff_drive_controller/cmd_vel` while publishing `/cmd_vel_lock` for the later mux integration.

### Verified

- `colcon build --packages-select sentinel_teleop sentinel_bringup` passed.
- `colcon test --packages-select sentinel_teleop sentinel_bringup` plus `colcon test-result --verbose` passed: 52 tests, 0 errors, 0 failures, 1 skipped.
- `ros2 launch sentinel_teleop gamepad.launch.py start_joy:=false` brought `/gamepad_interface` to lifecycle state `active`.
- Runtime parameter validation accepted `deadzone=0.12` and rejected `deadzone=0.9`.
- Synthetic `/joy` input with L1 held produced `/diff_drive_controller/cmd_vel` with `linear.x=0.45` and `angular.z=0.65`; releasing L1 produced zero velocity.
- Synthetic Square/ESTOP input published `/cmd_vel_lock` as `true` and `/rover_mode_request` with `MODE_ESTOP`.

## 2026-06-19 - Phase 4 ros2_control Configuration

### Added

- Added `sentinel_control/config/controllers.yaml` for controller manager, `joint_state_broadcaster`, `diff_drive_controller`, and `imu_sensor_broadcaster`.
- Added `sentinel_control/launch/control.launch.py` to spawn the validated controllers against `/controller_manager`, with launch switches for wheel controllers and the IMU broadcaster.
- Extended the robot Xacro with an IMU ros2_control sensor interface and a `gz_ros2_control` parameter-file hook.
- Added an optional `spawn_controllers` launch argument to `sentinel_gazebo/launch/sim.launch.py`.

### Changed

- Updated `README.md`, `docs/DEPENDENCIES.md`, and `docs/PHASE_TESTS.md` with Phase 4 controller dependency and validation notes.

### Verified

- `xacro` plus `check_urdf` still parse the robot model successfully after adding controller interfaces.
- `colcon build --packages-select sentinel_description sentinel_control sentinel_gazebo` passed.
- `colcon test --packages-select sentinel_description sentinel_control sentinel_gazebo` plus `colcon test-result --verbose` passed: 47 tests, 0 errors, 0 failures, 1 skipped.
- A clean simulation launch initialized `robot_state_publisher`, spawned `nexus_sentinel`, created the sensor bridges, and started the ros2_control controller manager.
- `joint_state_broadcaster` loaded, configured, and activated.
- `diff_drive_controller` loaded, configured, and activated.
- `imu_sensor_broadcaster` loaded, configured, and activated after aligning the ros2_control sensor name with Gazebo's `base_imu` sensor.
- `ros2 control list_hardware_interfaces --verbose` exposes the wheel velocity command interfaces, wheel position/velocity state interfaces, and `base_imu` orientation, angular velocity, and linear acceleration state interfaces.
- `/diff_drive_controller/odom`, `/diff_drive_controller/cmd_vel`, `/imu_sensor_broadcaster/imu`, `/joint_states`, `/tf`, and bridged `/imu` are available during the Phase 4 simulation run.
- Publishing a `geometry_msgs/msg/TwistStamped` command to `/diff_drive_controller/cmd_vel` changed odometry from near zero to approximately `x=0.099`, `y=0.009`, `yaw=8.6 deg`, and `tf2_echo odom base_footprint` reported the same transform.

## 2026-06-19 - Phase Test Playbook

### Added

- Added `docs/PHASE_TESTS.md` with copyable test commands for Phase 0 through Phase 10.
- Documented completed Phase 0-3 checks as runnable commands and expected results.
- Added future Phase 4-10 acceptance-test templates so each upcoming phase has an explicit operator-facing validation target.

### Changed

- Updated `README.md` to link the phase-by-phase test playbook.

## 2026-06-19 - Phase 3 Robot Description and Gazebo Simulation

### Added

- Added `sentinel_description/urdf/sentinel.urdf.xacro` with a parameterized differential-drive inspection robot, drive wheels, casters, lidar, camera, IMU, static sensor frames, and a `gz_ros2_control` system declaration.
- Added `sentinel_description/launch/description.launch.py` for publishing `robot_description` with `robot_state_publisher`.
- Added `sentinel_gazebo/worlds/sentinel_warehouse.sdf`, a simple warehouse/campus inspection world with walls, racks, a charging dock, and obstacles for later Nav2 work.
- Added `sentinel_gazebo/launch/sim.launch.py` to run Gazebo headless, spawn `nexus_sentinel`, and start ROS/Gazebo topic bridging.
- Added `sentinel_gazebo/config/bridge.yaml` for `/clock`, `/scan`, `/imu`, `/camera/image`, and `/camera/camera_info`.

### Changed

- Updated `sentinel_gazebo/package.xml` with `robot_state_publisher` and `xacro` runtime dependencies.
- Updated `README.md` and `docs/DEPENDENCIES.md` with Phase 3 simulation commands, observed topics, and URDF 1.2 compatibility notes.

### Verified

- Ran `xacro` and `check_urdf` on `sentinel.urdf.xacro`; the model parsed successfully with root link `base_footprint`.
- Ran `colcon build --packages-select sentinel_description sentinel_gazebo`: both packages finished successfully.
- Ran `colcon test --packages-select sentinel_description sentinel_gazebo` plus `colcon test-result --verbose`: 46 tests, 0 errors, 0 failures, 1 skipped.
- Ran a clean headless simulation launch and confirmed `create` reported `Entity creation successful`.
- Confirmed `ros2 topic list` included `/scan`, `/imu`, `/camera/image`, `/camera/camera_info`, `/joint_states`, `/tf`, and `/tf_static`.

### Notes

- The local Lyrical URDF parser did not expose confirmed `quat_xyzw` or `capsule` parsing support under `/opt/ros/lyrical`; Phase 3 therefore uses standard URDF `rpy` origins and primitive fallback collision geometry so the simulation remains runnable. The compatibility finding is recorded in `docs/DEPENDENCIES.md`.
- The installed `ros_gz_bridge` launch action rejected its own default `bridge_params` type in this environment, so `sim.launch.py` starts `parameter_bridge` directly with the validated YAML config file.

## 2026-06-19 - Phase 2 Custom Interfaces

### Added

- Added `sentinel_interfaces/msg/RoverMode.msg` with TELEOP, MAPPING, PATROL, and ESTOP constants.
- Added `sentinel_interfaces/msg/Waypoint.msg` with `name`, `geometry_msgs/Pose`, and `dwell_seconds` fields.
- Added `sentinel_interfaces/srv/SetMode.srv` for mode transition requests and current-mode responses.
- Added `sentinel_interfaces/action/PatrolRoute.action` for route patrol goals, results, and feedback.
- Enabled `rosidl_generate_interfaces` for C, C++, Python, and Rust interface generation in Lyrical.

### Changed

- Updated `sentinel_interfaces` package metadata with `rosidl_default_generators`, `rosidl_default_runtime`, and `rosidl_interface_packages` membership.
- Updated `README.md` and `docs/DEPENDENCIES.md` with the Phase 2 interface baseline.

### Verified

- Ran `ros2 interface show` for `RoverMode`, `Waypoint`, `SetMode`, and `PatrolRoute`; all matched the requested field design.
- Ran `colcon build`: 8 packages finished successfully.
- Ran `colcon test` plus `colcon test-result --verbose`: 40 tests, 0 errors, 0 failures, 1 skipped.

### Notes

- `member_of_group` must appear after dependency/test dependency elements in `package.xml` format 3; the order was corrected after xmllint caught the schema violation.

## 2026-06-19 - Phase 1 Package Skeletons

### Added

- Created the `src/` workspace tree.
- Added 8 ROS 2 package skeletons: `sentinel_interfaces`, `sentinel_description`, `sentinel_gazebo`, `sentinel_control`, `sentinel_teleop`, `sentinel_mission`, `sentinel_perception`, and `sentinel_bringup`.
- Added a Phase 1 `README.md` with current workspace layout and build/test commands.
- Added placeholder resource/config/launch directories for CMake packages and package-specific scaffold directories for later phases.

### Changed

- Simplified empty `ament_cmake` package skeletons so Phase 1 does not require later-phase runtime dependencies during CMake configure. Runtime dependencies remain declared in `package.xml` and will be activated in CMake as implementation is added.
- Replaced generated TODO package descriptions with project-specific descriptions.

### Verified

- Confirmed `c++` and `g++` are available after the operator installed the missing compiler toolchain.
- Ran `colcon build --event-handlers console_direct+`: 8 packages finished successfully.
- Ran `colcon test --event-handlers console_direct+` followed by `colcon test-result --verbose`: 40 tests, 0 errors, 0 failures, 1 skipped.

### Notes

- Phase 1 intentionally contains skeleton packages only. Custom interfaces start in Phase 2; robot description and simulation assets start in Phase 3.

## 2026-06-19 - Phase 0 Gazebo Baseline Correction

### Changed

- Re-sourced `/opt/ros/lyrical/setup.bash` and confirmed `gz` is available from the ROS vendored toolchain.
- Updated `docs/DEPENDENCIES.md` to record `gz sim --version` as `10.1.1` and `ros-lyrical-gz-ros2-control` as installed.

### Verified

- `command -v gz` returns `/opt/ros/lyrical/opt/gz_tools_vendor/bin/gz`.
- `gz sim --version` returns `10.1.1`.

## 2026-06-19 - Phase 0 Environment Baseline Refresh

### Changed

- Refreshed Phase 0 using ordinary `ssh nexus` as requested.
- Updated `docs/DEPENDENCIES.md` to reflect the current state: `colcon`, `jstest`, `evtest`, and the connected DualSense joystick devices are now available.
- Corrected Gazebo baseline: `gz` is available after sourcing `/opt/ros/lyrical/setup.bash`, and `gz sim --version` reports `10.1.1`.
- Recorded that `.gitignore` now ignores `build/`, `install/`, `log/`, `.DS_Store`, and editor backup files.

### Verified

- Confirmed target host `nexus` is Ubuntu 26.04 LTS (`resolute`) with ROS 2 Lyrical installed under `/opt/ros/lyrical`.
- Confirmed `ros2` works after sourcing `/opt/ros/lyrical/setup.bash`.
- Confirmed `colcon` is available at `/usr/bin/colcon`.
- Confirmed `colcon build` and `colcon test` both complete in the empty workspace.
- Confirmed the DualSense controller is trusted, connected, and exposes `/dev/input/js0` plus `/dev/input/js1`.
- Confirmed `/dev/input/js0` reports 8 axes and 13 buttons; `/dev/input/js1` reports 6 motion-sensor axes and 0 buttons.
- Confirmed GPU/display baseline: Intel Iris Xe, no NVIDIA tooling, Wayland local session, no `DISPLAY` in SSH shell.

### Blocked / Missing

- Gazebo is no longer considered blocked for Phase 0; later phases still need package-specific launch/integration validation.

## 2026-06-19 - Phase 0 Environment Baseline

### Added

- Initialized the `/home/zyx/ros2_ws` git repository on branch `main`.
- Added the Phase 0 environment baseline in `docs/DEPENDENCIES.md`.

### Verified

- Confirmed target host `nexus` is Ubuntu 26.04 LTS (`resolute`) with ROS 2 Lyrical installed under `/opt/ros/lyrical`.
- Confirmed `ros2` works after sourcing `/opt/ros/lyrical/setup.bash`.
- Confirmed the DualSense controller was paired but not connected during the first check, so no `/dev/input/js*` device was available at that time.
- Confirmed GPU/display baseline: Intel Iris Xe, no NVIDIA tooling, Wayland local session, no `DISPLAY` in SSH shell.
- Ran Phase 0 build/test verification commands; both initially stopped at `colcon: command not found` before the refresh showed `colcon` available.

### Blocked / Missing

- `colcon` was not found during the first pass, but is now available after the Phase 0 refresh.
- Gazebo is no longer considered blocked for Phase 0; later phases still need package-specific launch/integration validation.
- `jstest` and `evtest` were missing during the first pass, but are now available after the Phase 0 refresh.
