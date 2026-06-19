# Changelog

## 2026-06-19 - Phase 0 Environment Baseline Refresh

### Changed

- Refreshed Phase 0 using ordinary `ssh nexus` as requested.
- Updated `docs/DEPENDENCIES.md` to reflect the current state: `colcon`, `jstest`, `evtest`, and the connected DualSense joystick devices are now available.
- Recorded that Gazebo `gz` is still missing.
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

- Gazebo `gz` is not installed or not on `PATH`, so simulator version checks and later simulation phases are blocked.

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
- Gazebo `gz` is not installed or not on `PATH`, so simulator version checks and later simulation phases are blocked.
- `jstest` and `evtest` were missing during the first pass, but are now available after the Phase 0 refresh.
