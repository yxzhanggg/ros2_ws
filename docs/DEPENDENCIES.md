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
| Workspace state | Git repository on branch `main`; currently contains Phase 0 docs only |
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

### Gazebo / gz

| Item | Observed value |
| --- | --- |
| `gz` executable | Not found |
| `gz sim --version` | Could not run because `gz` is not installed or not on `PATH` |
| Installed gz-related packages | Only vendor packages were found: `ros-lyrical-gz-cmake-vendor`, `ros-lyrical-gz-math-vendor`, `ros-lyrical-gz-utils-vendor` |
| Result | Gazebo simulation phases are blocked until the simulator and ROS integration packages are installed |

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
| Gazebo `gz` simulator | Run `gz sim` and spawn the robot | Phase 3 onward |
| `gz_ros2_control` and related simulation integration | Connect Gazebo to `ros2_control` | Phase 3/4 |
| Nav2, slam_toolbox, twist_mux, controllers, and additional simulation packages | Required by architecture and later phases; package availability still needs complete verification before Phase 3+ | Phase 3 onward |

No network downloads, package installs, `sudo`, system service changes, udev rules, or user group changes were executed by Codex during this Phase 0 refresh.
