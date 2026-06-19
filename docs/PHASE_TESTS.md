# Phase Test Playbook

这份文档给操作者一组按 Phase 编排的可复制测试命令。Phase 0-3 已经完成，下面的命令应当可以在 `nexus` 上直接运行；Phase 4-10 是后续阶段的验收模板，等对应 Phase 实现后再运行，届时每个模板会根据实际代码继续更新成实测命令。

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

状态：待实现。完成后用下面命令验证 controller manager、差速控制器、IMU broadcaster、odom 和 TF。

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash

ros2 launch sentinel_gazebo sim.launch.py headless:=true &
launch_pid=$!
sleep 10

ros2 control list_controllers
ros2 topic list | sort | grep -E '^/odom$|^/tf$|^/joint_states$'
ros2 topic echo /odom --once
ros2 run tf2_ros tf2_echo odom base_link --once

ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.2, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"

sleep 2
ros2 topic echo /odom --once

kill -INT "${launch_pid}"
wait "${launch_pid}" || true
```

期望结果：

- `joint_state_broadcaster`、`diff_drive_controller`、`imu_sensor_broadcaster` 是 `active`
- `/odom` 持续发布
- `odom -> base_link` TF 可查询
- 发布 `/cmd_vel` 后 `/odom` 位姿或速度发生变化

## Phase 5 - DualSense Teleoperation

状态：待实现。完成后用下面命令验证 `joy`、`gamepad_interface`、模式按键、死人开关和急停 lock。

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash

ros2 launch sentinel_bringup teleop.launch.py &
launch_pid=$!
sleep 5

ros2 lifecycle get /gamepad_interface
ros2 topic echo /joy --once
ros2 topic echo /cmd_vel_teleop --once
ros2 topic echo /rover_mode --once
ros2 topic echo /cmd_vel_lock --once

ros2 param get /gamepad_interface deadzone
ros2 param set /gamepad_interface deadzone 0.12
ros2 param get /gamepad_interface deadzone

kill -INT "${launch_pid}"
wait "${launch_pid}" || true
```

期望结果：

- `/joy` 能收到 DualSense 输入
- 按住死人开关并推摇杆时 `/cmd_vel_teleop` 有非零速度
- 松开死人开关后 `/cmd_vel_teleop` 变为零速
- Square/方块键进入 ESTOP 并发布 lock
- 参数更新会经过 range 校验

## Phase 6 - Mission Management

状态：待实现。完成后用下面命令验证 `mode_manager` lifecycle、`SetMode` service、`PatrolRoute` action 和 mission logger。

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash

ros2 launch sentinel_bringup mission.launch.py &
launch_pid=$!
sleep 5

ros2 lifecycle get /mode_manager
ros2 service call /set_mode sentinel_interfaces/srv/SetMode "{mode: 0}"
ros2 topic echo /rover_mode --once

ros2 action list -t | grep PatrolRoute
ros2 action send_goal /patrol_route sentinel_interfaces/action/PatrolRoute \
  "{waypoints: [{name: 'dock', pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}, dwell_seconds: 1.0}], loop_forever: false}" \
  --feedback

ls -la log mission_logs 2>/dev/null || true

kill -INT "${launch_pid}"
wait "${launch_pid}" || true
```

期望结果：

- `/mode_manager` 可进入 active
- `/set_mode` 返回 success
- `/rover_mode` 使用 latched-style QoS，后启动的 echo 也能收到当前模式
- `PatrolRoute` action 有 feedback/result
- mission logger 写出结构化任务日志

## Phase 7 - Navigation And Mapping

状态：待实现。完成后用下面命令验证 slam_toolbox、Nav2 和巡逻路线闭环。

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

## Phase 8 - Perception And Composition

状态：待实现。完成后用下面命令验证 component container、intra-process 配置和感知输出。

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
ros2 topic echo /scan_filtered --once
ros2 topic echo /detections --once

kill -INT "${launch_pid}"
wait "${launch_pid}" || true
```

期望结果：

- 同一个 component container 内至少有两个 perception component
- 文档记录 intra-process 是否启用
- 感知输出 topic 能收到消息
- 无 GPU 环境下零拷贝/GPU demo 会优雅降级

## Phase 9 - Diagnostics, Observability, And Tests

状态：待实现。完成后用下面命令验证诊断、观测命令和集成测试。

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash

colcon test --event-handlers console_direct+
colcon test-result --verbose

ros2 doctor --report
ros2 topic list | sort
ros2 topic bw /scan
ros2 service list -t
ros2 service info /set_mode --verbose

ros2 topic echo /diagnostics --once
```

期望结果：

- 全工作区测试通过
- launch_testing 集成测试覆盖仿真关键话题/服务/action
- `/diagnostics` 至少包含电池和控制器健康状态
- 文档中记录 `ros2 doctor`、`ros2 topic bw`、`ros2 service info --verbose` 的实际输出示例

## Phase 10 - Documentation

状态：待实现。完成后用下面命令确认最终文档完整性和快速上手路径。

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
```

期望结果：

- README 能让新操作者在 15 分钟内启动仿真并用手柄测试
- `docs/ENGINEERING.md` 覆盖架构、接口、QoS、测试策略、排障和扩展
- `docs/LEARN_ROS2.md` 用本项目实际文件解释 ROS 2 概念并带自测题
- 本文档覆盖所有 Phase 的测试命令
