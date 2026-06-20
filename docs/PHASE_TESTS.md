# Phase Test Playbook

这份文档给操作者一组按 Phase 编排的可复制测试命令。Phase 0-10 已经完成到当前定义的可运行基线，下面的命令应当可以在 `nexus` 上直接运行。

通用准备命令：

```bash
ssh nexus
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
```

如果命令需要访问当前工作区构建产物，再加：

```bash
source install/setup.bash
```

## Phase 0 - Environment Baseline

目标：确认 ROS 2、Gazebo、构建工具、DualSense 手柄、GPU/显示环境可被系统识别。

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash

echo "ROS_DISTRO=${ROS_DISTRO}"
command -v ros2
ros2 --help >/tmp/sentinel_phase0_ros2_help.txt

command -v colcon
colcon build
colcon test

command -v gz
gz sim --version

ls -l /dev/input/js* || true
jstest --normal /dev/input/js0 | head -n 8
jstest --normal /dev/input/js1 | head -n 8

lspci | grep -i 'vga\|3d\|display' || true
echo "DISPLAY=${DISPLAY}"
```

期望结果：

- `ROS_DISTRO=lyrical`
- `gz sim --version` 输出 `10.1.1`
- `colcon build` 和 `colcon test` 在空/基础工作区可完成
- `/dev/input/js0` 是 DualSense controller，`/dev/input/js1` 是 motion sensors

## Phase 1 - Workspace And Package Skeletons

目标：确认 8 个 `sentinel_*` 包存在并且全工作区能构建、测试。

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash

find src -maxdepth 1 -type d -name 'sentinel_*' | sort

colcon build --event-handlers console_direct+
colcon test --event-handlers console_direct+
colcon test-result --verbose
```

期望结果：

- 看到 `sentinel_interfaces`、`sentinel_description`、`sentinel_gazebo`、`sentinel_control`、`sentinel_teleop`、`sentinel_mission`、`sentinel_perception`、`sentinel_bringup`
- 当前 Phase 3 状态下，全工作区测试汇总为 `46 tests, 0 errors, 0 failures, 1 skipped`

## Phase 2 - Custom Interfaces

目标：确认自定义 msg/srv/action 可以被 ROS 2 正确发现和展示。

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash

ros2 interface show sentinel_interfaces/msg/RoverMode
ros2 interface show sentinel_interfaces/msg/Waypoint
ros2 interface show sentinel_interfaces/srv/SetMode
ros2 interface show sentinel_interfaces/action/PatrolRoute

colcon build --packages-select sentinel_interfaces --event-handlers console_direct+
colcon test --packages-select sentinel_interfaces --event-handlers console_direct+
colcon test-result --verbose
```

期望结果：

- `RoverMode` 包含 `MODE_TELEOP`、`MODE_MAPPING`、`MODE_PATROL`、`MODE_ESTOP`
- `Waypoint` 包含 `string name`、`geometry_msgs/Pose pose`、`float32 dwell_seconds`
- `SetMode` 和 `PatrolRoute` 字段与接口设计一致

## Phase 3 - Robot Description And Gazebo Simulation

目标：确认 Xacro 能展开、URDF 能解析、Gazebo 能 headless 启动并 spawn 机器人，传感器话题能出现在 ROS 2 中。

### Model Check

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash

xacro src/sentinel_description/urdf/sentinel.urdf.xacro use_sim:=true >/tmp/sentinel.urdf
check_urdf /tmp/sentinel.urdf
```

期望结果：`check_urdf` 输出 `Successfully Parsed XML`，root link 是 `base_footprint`。

### Package Check

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash

colcon build --packages-select sentinel_description sentinel_gazebo --event-handlers console_direct+
colcon test --packages-select sentinel_description sentinel_gazebo --event-handlers console_direct+
colcon test-result --verbose
```

期望结果：相关包构建和测试均通过。

### Headless Simulation Smoke Test

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash

ros2 launch sentinel_gazebo sim.launch.py headless:=true >/tmp/sentinel_phase3_launch.log 2>&1 &
launch_pid=$!

sleep 12
ros2 topic list | sort

kill -INT "${launch_pid}"
wait "${launch_pid}" || true

sed -n '1,180p' /tmp/sentinel_phase3_launch.log
```

期望结果：

- launch log 中有 `Robot initialized`
- launch log 中有 `Entity creation successful`
- `ros2 topic list` 包含 `/scan`、`/imu`、`/camera/image`、`/camera/camera_info`、`/joint_states`、`/tf`、`/tf_static`

如果 Gazebo 没有在 `Ctrl+C` 后干净退出，可以只清理本次测试启动的相关进程：

```bash
ps -eo pid,ppid,cmd | grep -E 'sentinel_gazebo sim.launch|gz sim|ruby.*gz|parameter_bridge|robot_state_publisher' | grep -v grep
```

确认 PID 属于本次测试后再结束它们。

## Phase 4 - ros2_control

目标：验证 controller manager、joint state broadcaster、差速控制器、IMU broadcaster、odom、TF 和差速控制链路。Lyrical 当前 `diff_drive_controller` 使用 namespaced `TwistStamped` 输入：`/diff_drive_controller/cmd_vel`。

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash

ros2 launch sentinel_gazebo sim.launch.py headless:=true spawn_controllers:=true &
launch_pid=$!
sleep 12

ros2 control list_controllers || ros2 service list | grep controller_manager
ros2 topic list -t | sort | grep -E 'diff_drive_controller/(cmd_vel|odom)|imu_sensor_broadcaster/imu|^/imu|^/tf|^/joint_states'
ros2 topic echo /diff_drive_controller/odom --once
timeout 5s ros2 run tf2_ros tf2_echo odom base_footprint -r 1

ros2 topic pub --once /diff_drive_controller/cmd_vel geometry_msgs/msg/TwistStamped \
  "{header: {frame_id: base_footprint}, twist: {linear: {x: 0.2, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.3}}}"

sleep 2
ros2 topic echo /diff_drive_controller/odom --once

kill -INT "${launch_pid}"
wait "${launch_pid}" || true
```

期望结果：

- `joint_state_broadcaster`、`diff_drive_controller`、`imu_sensor_broadcaster` 是 `active`
- `/diff_drive_controller/odom` 持续发布
- `odom -> base_footprint` TF 可查询
- 发布 `/diff_drive_controller/cmd_vel` 后 `/diff_drive_controller/odom` 位姿发生变化
- `/imu_sensor_broadcaster/imu` 和 Gazebo bridge 的 `/imu` 都发布 `sensor_msgs/msg/Imu`

## Phase 5 - DualSense Teleoperation

目标：验证 `joy_node`、`gamepad_interface` lifecycle、DualSense 轴/按键映射、死人开关、ESTOP lock、参数 range 校验，以及遥控命令能进入 Phase 4 的差速控制器。

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash

ros2 launch sentinel_bringup teleop.launch.py &
launch_pid=$!
sleep 18

ros2 lifecycle get /gamepad_interface
ros2 topic list -t | sort | grep -E '^/joy|diff_drive_controller/cmd_vel|^/cmd_vel_lock|^/rover_mode_request|record_request'
ros2 topic echo /joy --once
ros2 topic echo /diff_drive_controller/cmd_vel --once
ros2 topic echo /rover_mode_request --once
ros2 topic echo /cmd_vel_lock --once

ros2 param get /gamepad_interface deadzone
ros2 param set /gamepad_interface deadzone 0.12
ros2 param get /gamepad_interface deadzone
ros2 param set /gamepad_interface deadzone 0.9 || true

kill -INT "${launch_pid}"
wait "${launch_pid}" || true
```

期望结果：

- `/joy` 能收到 DualSense 输入。
- `/gamepad_interface` 自动进入 `active`。
- 按住 L1 死人开关、推左摇杆/右摇杆，并按 R2 调速时，`/diff_drive_controller/cmd_vel` 有非零 `TwistStamped`。
- 松开 L1 后 `/diff_drive_controller/cmd_vel` 变为零速。
- Square/方块键进入 ESTOP 并通过 `/cmd_vel_lock` 发布 `true`；R1 清除 ESTOP。
- `deadzone=0.12` 能设置成功，`deadzone=0.9` 被 range 校验拒绝。
- Create/Options 只发布 `/record_request` 和 `/stop_record_request` 请求；真正调用 rosbag2 远程 service 会在 mission logger 阶段接入。

不想手动按手柄时，可以用下面的可重复合成输入测试 `gamepad_interface`：

```bash
ros2 launch sentinel_teleop gamepad.launch.py start_joy:=false &
launch_pid=$!
sleep 8

ros2 lifecycle get /gamepad_interface
ros2 param set /gamepad_interface deadzone 0.9 || true

ros2 topic echo /diff_drive_controller/cmd_vel --once &
echo_pid=$!
sleep 1
ros2 topic pub /joy sensor_msgs/msg/Joy --times 5 -r 10 \
  "{axes: [0.0, -1.0, 0.0, -0.5, 0.0, -1.0, 0.0, 0.0], buttons: [0,0,0,0,1,0,0,0,0,0,0,0,0]}"
wait "${echo_pid}" || true

ros2 topic echo /diff_drive_controller/cmd_vel --once &
echo_pid=$!
sleep 1
ros2 topic pub /joy sensor_msgs/msg/Joy --times 5 -r 10 \
  "{axes: [0.0, -1.0, 0.0, -0.5, 0.0, -1.0, 0.0, 0.0], buttons: [0,0,0,0,0,0,0,0,0,0,0,0,0]}"
wait "${echo_pid}" || true

ros2 topic echo /cmd_vel_lock --once &
lock_pid=$!
ros2 topic echo /rover_mode_request --once &
mode_pid=$!
sleep 1
ros2 topic pub /joy sensor_msgs/msg/Joy --times 5 -r 10 \
  "{axes: [0.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0], buttons: [0,0,1,0,0,0,0,0,0,0,0,0,0]}"
wait "${lock_pid}" || true
wait "${mode_pid}" || true

kill -INT "${launch_pid}"
wait "${launch_pid}" || true
```

当前 `nexus` 实测：L1 合成输入输出 `linear.x=0.45`、`angular.z=0.65`；松开 L1 输出零速；Square 输出 `/cmd_vel_lock: true` 和 `MODE_ESTOP`。

## Phase 6 - Mission Management

目标：验证 `mode_manager` lifecycle、latched-style `/rover_mode`、`SetMode` service、`PatrolRoute` action 和 mission logger JSONL 输出。

### Package Check

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash

colcon build --packages-select sentinel_mission sentinel_bringup --event-handlers console_direct+
colcon test --packages-select sentinel_mission sentinel_bringup --event-handlers console_direct+
colcon test-result --verbose
```

期望结果：相关包构建和测试均通过。当前 `nexus` 实测汇总为 `75 tests, 0 errors, 0 failures, 4 skipped`。

### Runtime Smoke Test

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash

ros2 launch sentinel_bringup mission.launch.py &
launch_pid=$!
sleep 5

ros2 lifecycle get /mode_manager
ros2 topic echo /rover_mode --once
ros2 service call /set_mode sentinel_interfaces/srv/SetMode "{mode: 1}"
ros2 topic echo /rover_mode --once

ros2 action list -t | grep patrol_route
ros2 action send_goal /patrol_route sentinel_interfaces/action/PatrolRoute \
  "{waypoints: [{name: dock, pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}, dwell_seconds: 0.2}], loop_forever: false}" \
  --feedback

tail -n 20 log/mission_events.jsonl

kill -INT "${launch_pid}"
wait "${launch_pid}" || true
```

期望结果：

- `/mode_manager` 是 `active`
- 第一次 `/rover_mode` echo 能收到当前 `TELEOP`
- `/set_mode` 返回 `success=True`，第二次 `/rover_mode` echo 能收到 `MAPPING`
- `/patrol_route` action 有 feedback，并以 `SUCCEEDED` 结束，`waypoints_completed: 1`
- `log/mission_events.jsonl` 包含 `MAPPING`、`PATROL`、`TELEOP` 三类 mode 事件

当前 `nexus` 实测：`/set_mode` 将模式切到 `MAPPING`；单 waypoint `dock` action 成功完成；mission log 记录 `MAPPING -> PATROL -> TELEOP`。由于 Nav2 尚未安装，Phase 6 的 patrol 执行是 mission-manager simulation mode，真实 Nav2 路线执行留到 Phase 7。

## Phase 7 - Navigation And Mapping

状态：工程基线已实现，完整 SLAM/Nav2 运行被当前系统依赖阻塞。当前 `nexus` 缺少 `slam_toolbox`、`nav2_bringup`、`nav2_msgs`，`twist_mux` 有 apt 候选但尚未安装。

### Package Check

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash

colcon build --packages-select sentinel_bringup --event-handlers console_direct+
colcon test --packages-select sentinel_bringup --event-handlers console_direct+
colcon test-result --verbose
```

期望结果：`sentinel_bringup` 构建和测试通过。当前 `nexus` 实测汇总为 `84 tests, 0 errors, 0 failures, 4 skipped`。

### Dependency Smoke Test

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash

ros2 launch sentinel_bringup mapping.launch.py start_sim:=false start_joy:=false
ros2 launch sentinel_bringup nav.launch.py start_sim:=false start_mission:=false
```

当前期望结果：

- mapping launch 明确提示缺少 `slam_toolbox` 和 `twist_mux`
- nav launch 明确提示缺少 `nav2_bringup`、`nav2_msgs` 和 `twist_mux`
- launch 不会半启动仿真或导航进程

### Full Runtime Test After Dependencies Are Installed

等 `slam_toolbox`、Nav2 和 `twist_mux` 安装并重新 `source install/setup.bash` 后，再运行下面的完整验收命令。

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash

ros2 launch sentinel_bringup mapping.launch.py &
mapping_pid=$!
sleep 10

ros2 node list | grep -E 'slam|map'
ros2 topic list | grep -E '^/map$|^/scan$'
ros2 topic echo /map --once

ros2 service call /serialize_map slam_toolbox/srv/SerializePoseGraph \
  "{filename: '/tmp/sentinel_test_map'}" || true

kill -INT "${mapping_pid}"
wait "${mapping_pid}" || true

ros2 launch sentinel_bringup nav.launch.py map:=/tmp/sentinel_test_map.yaml &
nav_pid=$!
sleep 10

ros2 node list | grep -E 'bt_navigator|controller_server|planner_server|behavior_server|waypoint_follower'
ros2 action list -t | grep -E 'Navigate|FollowWaypoints'

kill -INT "${nav_pid}"
wait "${nav_pid}" || true
```

期望结果：

- 建图模式能发布 `/map`
- Nav2 关键节点启动
- Nav2 action server 可见
- 后续巡逻 action 能驱动机器人完成一条路线

Phase 7 已经提供：

- `sentinel_bringup/launch/mapping.launch.py`
- `sentinel_bringup/launch/nav.launch.py`
- `sentinel_bringup/config/slam_toolbox.yaml`
- `sentinel_bringup/config/nav2.yaml`
- `sentinel_bringup/config/twist_mux.yaml`
- `sentinel_bringup/maps/sentinel_phase7_demo.yaml`
- `sentinel_bringup/routes/warehouse_loop.yaml`

## Phase 8 - Perception And Composition

目标：验证 `sentinel_perception` 的 C++ component library、同进程 component container、intra-process 配置、`/scan_filtered` 和 `/detections` 输出。

### Package Check

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash

colcon build --packages-select sentinel_perception --event-handlers console_direct+
colcon test --packages-select sentinel_perception --event-handlers console_direct+
colcon test-result --verbose
```

期望结果：`sentinel_perception` 构建和测试通过。当前 `nexus` 实测汇总为 `108 tests, 0 errors, 0 failures, 8 skipped`。

### Runtime Smoke Test

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash

ros2 launch sentinel_perception perception.launch.py &
launch_pid=$!
sleep 5

ros2 component list
ros2 node info /sentinel_perception_container
ros2 topic list | grep -E 'scan_filtered|detections|camera'

timeout 8s ros2 topic echo /scan_filtered --once > /tmp/sentinel_scan_filtered.txt &
scan_echo=$!
sleep 1
ros2 topic pub /scan sensor_msgs/msg/LaserScan --once \
  "{header: {frame_id: lidar_link}, angle_min: 0.0, angle_max: 0.3, angle_increment: 0.1, time_increment: 0.0, scan_time: 0.1, range_min: 0.05, range_max: 20.0, ranges: [0.01, 1.0, 99.0, 2.0], intensities: []}"
wait "${scan_echo}"
cat /tmp/sentinel_scan_filtered.txt

timeout 8s ros2 topic echo /detections --once > /tmp/sentinel_detection.txt &
det_echo=$!
sleep 1
ros2 topic pub /camera/image sensor_msgs/msg/Image --once \
  "{header: {frame_id: camera_link}, height: 1, width: 4, encoding: mono8, is_bigendian: 0, step: 4, data: [255, 255, 255, 255]}"
wait "${det_echo}"
cat /tmp/sentinel_detection.txt

kill -INT "${launch_pid}"
wait "${launch_pid}" || true
```

期望结果：

- 同一个 component container 内至少有两个 perception component
- `/sentinel_perception_container` 内有 `/scan_filter` 和 `/image_marker_detector`
- `/scan_filtered` 能收到 `sensor_msgs/msg/LaserScan`，无效/越界 ranges 会被夹到 `max_range_m=12.0`
- `/detections` 能收到 JSON 字符串，synthetic bright image 会输出 `bright_marker: true`
- Phase 0 未检测到 NVIDIA/CUDA，因此 Phase 8 使用 CPU intra-process component path，GPU/rosidl buffer zero-copy demo 记录为 disabled

## Phase 9 - Diagnostics, Observability, And Tests

目标：验证 `diagnostic_updater` 诊断输出、`launch_testing` 集成测试、以及 ROS 2 观测命令示例。

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash

colcon build --packages-select sentinel_mission --event-handlers console_direct+
colcon test --packages-select sentinel_mission --event-handlers console_direct+
colcon test-result --verbose
```

期望结果：`sentinel_mission` 构建和测试通过，包含 `test_mission_diagnostics_launch.py`。当前 `nexus` 实测汇总为 `116 tests, 0 errors, 0 failures, 8 skipped`。

### Diagnostics Smoke Test

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash

ros2 launch sentinel_mission diagnostics.launch.py &
launch_pid=$!
sleep 3

ros2 topic echo /diagnostics --once

kill -INT "${launch_pid}"
wait "${launch_pid}" || true
```

期望结果：

- `/diagnostics` 包含 `health_monitor: battery`
- `/diagnostics` 包含 `health_monitor: controller`
- battery message 是 `battery nominal`
- controller message 是 `controller heartbeat nominal`

### Observability Commands

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash

ros2 doctor --report | sed -n '1,80p'

ros2 launch sentinel_bringup mission.launch.py &
launch_pid=$!
sleep 5

ros2 service info /set_mode --verbose
timeout 5s ros2 topic bw /diagnostics || true

kill -INT "${launch_pid}"
wait "${launch_pid}" || true
```

当前 `nexus` 实测摘录：

```text
ros2 doctor --report:
ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET, ROS_DISTRO=lyrical
network device wlp0s20f3 inet 192.168.1.17

ros2 service info /set_mode --verbose:
Type: sentinel_interfaces/srv/SetMode
Node name: mode_manager
Service type hash: RIHS01_c821b3398626b934653ca8c463691318d057d3e7d5d9f2bc549cc2ac6e33c7a9
Reliability: RELIABLE
Durability: VOLATILE

ros2 topic bw /diagnostics:
1.46 KB/s from 3 messages
1.22 KB/s from 6 messages
1.15 KB/s from 9 messages
Message size mean: 0.35 KB
```

期望结果：

- `ros2 doctor --report` 能输出 ROS 环境、网络和包版本信息
- `/set_mode --verbose` 能展示 service type、endpoint 和 QoS
- `/diagnostics` 带宽能采样到持续发布的诊断消息
- `timeout` 结束 `ros2 topic bw` 时可能打印 shutdown wait-set 警告，采样行仍有效

## Phase 10 - Documentation

目标：确认最终文档完整性、受众区分和快速上手路径。

```bash
cd ~/ros2_ws

test -f README.md
test -f docs/ENGINEERING.md
test -f docs/LEARN_ROS2.md
test -f docs/DEPENDENCIES.md
test -f docs/CHANGELOG.md
test -f docs/PHASE_TESTS.md

grep -n "Phase 0" docs/PHASE_TESTS.md
grep -n "Phase 10" docs/PHASE_TESTS.md
grep -n "概念" docs/ENGINEERING.md
grep -n "自测" docs/LEARN_ROS2.md
grep -n "Quick Start" README.md
grep -n "Documentation" README.md
grep -n "Nexus Sentinel 工程文档" docs/ENGINEERING.md
grep -n "跟着 Nexus Sentinel 学 ROS 2" docs/LEARN_ROS2.md
```

期望结果：

- README 能让新操作者在 15 分钟内启动仿真并用手柄测试
- `docs/ENGINEERING.md` 覆盖架构、接口、QoS、测试策略、排障和扩展
- `docs/LEARN_ROS2.md` 用本项目实际文件解释 ROS 2 概念并带自测题
- 本文档覆盖所有 Phase 的测试命令

当前 `nexus` 实测：上述文件存在性和 grep 检查均通过。
