# Changelog

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
