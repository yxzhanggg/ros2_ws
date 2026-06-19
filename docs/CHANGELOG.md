# Changelog

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
