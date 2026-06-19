# Dependencies and Environment Baseline

This document records the real environment observed during Phase 0. It is intentionally factual: missing tools and blocked checks are listed as issues to resolve before later phases.

## Phase 0 Environment Baseline

Checked at: 2026-06-19T18:32:20+08:00

### Host

| Item | Observed value |
| --- | --- |
| Target host | `nexus` |
| OS | Ubuntu 26.04 LTS (`resolute`) |
| Kernel | `Linux nexus 7.0.0-22-generic #22-Ubuntu SMP PREEMPT_DYNAMIC Mon May 25 15:54:34 UTC 2026 x86_64 GNU/Linux` |
| Workspace | `/home/zyx/ros2_ws` |
| Workspace initial state | Existing directory, empty before Phase 0 documentation, no git repository |
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
| `ros2 doctor --report` warnings | `PackageReport` and `RosdistroReport` functions failed; endpoint lists were empty because no ROS graph was running |

Command pattern required for later phases:

```bash
source /opt/ros/lyrical/setup.bash
```

### Build Tooling

| Tool | Observed value |
| --- | --- |
| `colcon` | Not found in `PATH`, even after sourcing `/opt/ros/lyrical/setup.bash` |
| Result | Phase 1+ builds cannot run until colcon is installed or otherwise made available |

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
| Pairing state | Paired: yes; Bonded: yes; Trusted: no; Blocked: no; Connected: no |
| `/dev/input/js*` | No joystick devices found |
| `/dev/input/by-id` | Not present during the check |
| `/dev/input/event*` | Event devices exist and are owned by `root:input`, but no DualSense js device was exposed because the controller was not connected |
| `jstest` / `evtest` | Not found |
| Installed ROS joystick package | `ros-lyrical-joy 3.3.0-4resolute.20260606.031052` is installed |
| Additional teleop package | `ros-lyrical-teleop-twist-joy 2.6.5-3resolute.20260606.031807` is installed, but the project will still implement its own `gamepad_interface` node as required |

System-level follow-up commands that require explicit approval before execution:

```bash
sudo apt install joystick evtest
```

Potential controller follow-up, also user-session sensitive and not executed in Phase 0:

```bash
bluetoothctl trust AC:36:1B:17:37:A3
bluetoothctl connect AC:36:1B:17:37:A3
```

If joystick access fails after the controller is connected, input-group or udev changes may be needed. Those are explicitly outside the allowed autonomous scope and require prior approval.

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

The Codex app is running on macOS, but the target ROS machine is reachable via SSH as `nexus`. Plain SSH sometimes tried IPv6 and failed with `Undefined error: 0`; forcing IPv4 was reliable during Phase 0:

```bash
ssh -o AddressFamily=inet nexus hostname
```

Later remote commands should use the same option unless DNS/IPv6 behavior is fixed.

## Missing Dependencies Identified in Phase 0

These items are required for later phases but were not installed or not usable during Phase 0:

| Dependency | Why it is needed | Phase affected |
| --- | --- | --- |
| `colcon` / `python3-colcon-common-extensions` | Build and test ROS 2 workspaces | Phase 1 onward |
| Gazebo `gz` simulator | Run `gz sim` and spawn the robot | Phase 3 onward |
| `gz_ros2_control` and related simulation integration | Connect Gazebo to `ros2_control` | Phase 3/4 |
| `joystick` / `evtest` | Verify DualSense axes/buttons from `/dev/input` | Phase 0/5 |
| Connected DualSense input device | Required for actual teleop validation | Phase 5 |
| Nav2, slam_toolbox, twist_mux, controllers, RViz packages | Required by architecture and later phases; package availability still needs complete verification after tooling is fixed | Phase 3 onward |

No network downloads, package installs, `sudo`, system service changes, udev rules, or user group changes were executed during Phase 0.
