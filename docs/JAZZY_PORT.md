# Ubuntu 24.04 / ROS 2 Jazzy Port Notes

This branch targets Ubuntu 24.04 and ROS 2 Jazzy. It was created from the validated `ubuntu26-ros2-lyrical` branch.

The source has been adjusted to avoid hard dependencies on APIs that were observed on the Lyrical host:

- `mission_logger.py` now falls back from `rclpy.experimental.AsyncNode` to a standard `rclpy.node.Node` plus an asyncio-friendly executor loop.
- `mode_manager_main.cpp` uses `rclcpp::executors::MultiThreadedExecutor` instead of the Lyrical experimental `EventsExecutor`.
- `sentinel_gazebo/launch/sim.launch.py` no longer hard-codes `gz_version:=10`.
- Phase 7 dependency messages now refer to Jazzy packages.

## Install Commands

On Ubuntu 24.04 with ROS 2 Jazzy configured:

```bash
sudo apt-get update
sudo apt-get install -y \
  python3-colcon-common-extensions \
  python3-rosdep \
  ros-jazzy-ros-base \
  ros-jazzy-ros-gz \
  ros-jazzy-ros-gz-sim \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-gz-ros2-control \
  ros-jazzy-xacro \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-ros2-control \
  ros-jazzy-ros2-controllers \
  ros-jazzy-ros2controlcli \
  ros-jazzy-controller-manager \
  ros-jazzy-joint-state-broadcaster \
  ros-jazzy-diff-drive-controller \
  ros-jazzy-imu-sensor-broadcaster \
  ros-jazzy-joy \
  ros-jazzy-diagnostic-updater \
  ros-jazzy-rclcpp-components \
  ros-jazzy-twist-mux \
  ros-jazzy-twist-mux-msgs
```

For full Phase 7 runtime, install the Jazzy navigation and SLAM packages if available in your apt index:

```bash
sudo apt-get install -y \
  ros-jazzy-navigation2 \
  ros-jazzy-nav2-bringup \
  ros-jazzy-nav2-msgs \
  ros-jazzy-slam-toolbox
```

If any package is missing from apt, do not fake the runtime result. Record the missing package and either use the closest supported Jazzy package set or build the dependency from source in an approved workspace/vendor flow.

## Build And Test

```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash

rosdep update
rosdep install --from-paths src --ignore-src -r -y

colcon build --event-handlers console_direct+
source install/setup.bash
colcon test --event-handlers console_direct+
colcon test-result --verbose
```

## Jazzy Retest Checklist

- Confirm `ROS_DISTRO=jazzy`.
- Confirm `gz sim --version` and update Gazebo notes if the major version differs.
- Confirm `diff_drive_controller` command topic type. If Jazzy expects `geometry_msgs/msg/Twist` instead of `TwistStamped`, update `gamepad_interface`, `twist_mux.yaml`, and tests together.
- Confirm `ros_gz_bridge` launch/config behavior.
- Confirm `mission_logger` works with or without `AsyncNode`.
- Confirm `mode_manager` builds with `MultiThreadedExecutor`.
- Confirm `twist_mux` remappings and lock topic behavior.
- Confirm `slam_toolbox` and Nav2 launch correctly before claiming full Phase 7 acceptance.

## Branch Relationship

- `ubuntu26-ros2-lyrical`: validated original branch on the `nexus` host.
- `ubuntu24-ros2-jazzy`: this source port branch.
- `main`: minimal standard ROS 2 workspace template, not the full robot implementation.
