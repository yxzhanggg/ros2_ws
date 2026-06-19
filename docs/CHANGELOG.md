# Changelog

## 2026-06-19 - Phase 0 Environment Baseline

### Added

- Initialized the `/home/zyx/ros2_ws` git repository on branch `main`.
- Added the Phase 0 environment baseline in `docs/DEPENDENCIES.md`.

### Verified

- Confirmed target host `nexus` is Ubuntu 26.04 LTS (`resolute`) with ROS 2 Lyrical installed under `/opt/ros/lyrical`.
- Confirmed `ros2` works after sourcing `/opt/ros/lyrical/setup.bash`.
- Confirmed the DualSense controller is paired but not connected, so no `/dev/input/js*` device is currently available.
- Confirmed GPU/display baseline: Intel Iris Xe, no NVIDIA tooling, Wayland local session, no `DISPLAY` in SSH shell.
- Ran Phase 0 build/test verification commands; both stopped at `colcon: command not found`.

### Blocked / Missing

- `colcon` is not installed or not on `PATH`, so Phase 0 build/test commands could not complete.
- Gazebo `gz` is not installed or not on `PATH`, so simulator version checks and later simulation phases are blocked.
- `jstest` and `evtest` are missing; installing them requires explicit approval.
