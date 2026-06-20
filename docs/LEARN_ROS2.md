# 跟着 Nexus Sentinel 学 ROS 2

这份教程面向 ROS 2 新手。你只需要会基本命令行：`cd`、`ls`、复制粘贴命令。学习节奏是：先讲概念，再在本项目里指给你看，最后给一个小练习。

## 1. ROS 2 是什么

ROS 2 可以把机器人软件拆成很多小程序，这些小程序叫 node。node 之间通过 topic、service、action、parameter、TF 等机制协作。Nexus Sentinel 的故事是：一台仓库/园区巡检机器人可以在 Gazebo 里仿真，用 DualSense 手柄驾驶，也能发布任务状态、传感器数据和诊断信息。

先准备环境：

```bash
ssh nexus
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
source install/setup.bash
```

自测：

1. ROS 2 里运行中的小程序通常叫什么？
2. 为什么每次新 shell 都要 `source /opt/ros/lyrical/setup.bash`？
3. Nexus Sentinel 的工作区路径是什么？

## 2. 工作区与包

ROS 2 workspace 是一组 package 的集合。本项目的 workspace 是 `~/ros2_ws`，源码都在 `src/` 下。

```bash
find src -maxdepth 1 -type d -name 'sentinel_*' | sort
```

你会看到这些包：

- `sentinel_interfaces`：自定义接口
- `sentinel_description`：机器人模型
- `sentinel_gazebo`：仿真世界
- `sentinel_control`：控制器配置
- `sentinel_teleop`：手柄遥控
- `sentinel_mission`：任务、日志、诊断
- `sentinel_perception`：传感器处理组件
- `sentinel_bringup`：顶层 launch

构建命令：

```bash
colcon build --packages-select sentinel_interfaces
```

自测：

1. `src/sentinel_teleop` 负责什么？
2. `colcon build --packages-select sentinel_interfaces` 只构建哪个包？
3. 顶层 launch 通常放在哪个包？

## 3. 节点与话题

Topic 像广播频道。一个 node 发布消息，另一个 node 订阅消息。手柄节点把 `/joy` 转成速度命令，感知组件把 `/scan` 转成 `/scan_filtered`。

运行感知组件：

```bash
ros2 launch sentinel_perception perception.launch.py
```

另开一个 shell：

```bash
ros2 topic list | grep -E 'scan_filtered|detections'
```

发布一条假的激光数据：

```bash
ros2 topic pub /scan sensor_msgs/msg/LaserScan --once \
  "{header: {frame_id: lidar_link}, angle_min: 0.0, angle_max: 0.3, angle_increment: 0.1, time_increment: 0.0, scan_time: 0.1, range_min: 0.05, range_max: 20.0, ranges: [0.01, 1.0, 99.0, 2.0], intensities: []}"
```

查看输出：

```bash
ros2 topic echo /scan_filtered --once
```

代码位置：

- `src/sentinel_perception/src/scan_filter_component.cpp`
- `src/sentinel_perception/launch/perception.launch.py`

自测：

1. `/scan_filtered` 是 topic、service 还是 action？
2. 为什么传感器 topic 通常使用 SensorDataQoS？
3. `ScanFilterComponent` 收到越界 range 后做了什么？

## 4. Service 与参数

Service 像一次请求/响应。`/set_mode` 用来切换机器人模式。

启动 mission：

```bash
ros2 launch sentinel_bringup mission.launch.py
```

另开 shell 调用 service：

```bash
ros2 service call /set_mode sentinel_interfaces/srv/SetMode "{mode: 1}"
ros2 topic echo /rover_mode --once
```

参数是 node 的配置。手柄死区在这里：

```bash
sed -n '1,80p' src/sentinel_teleop/config/gamepad.yaml
```

运行时改参数：

```bash
ros2 param set /gamepad_interface deadzone 0.12
```

代码位置：

- `src/sentinel_mission/src/mode_manager.cpp`
- `src/sentinel_teleop/sentinel_teleop/gamepad_interface.py`

自测：

1. `/set_mode` 的请求字段叫什么？
2. `mode: 1` 对应哪个模式？
3. 参数文件为什么比硬编码更容易调试？

## 5. Action

Action 适合“会持续一段时间、有反馈、有结果”的任务。巡逻路线就是 action。

```bash
ros2 action send_goal /patrol_route sentinel_interfaces/action/PatrolRoute \
  "{waypoints: [{name: dock, pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}, dwell_seconds: 0.2}], loop_forever: false}" \
  --feedback
```

当前没有 Nav2，所以 Phase 6 的 action 是 mission-manager simulation mode：它会发布反馈并返回成功，但不会真的调用 Nav2。

代码位置：

- `src/sentinel_interfaces/action/PatrolRoute.action`
- `src/sentinel_mission/src/mode_manager.cpp`

自测：

1. Action 和 service 最大区别是什么？
2. `PatrolRoute` feedback 里有哪些字段？
3. 当前为什么还没有真实 Nav2 巡逻？

## 6. TF 与机器人描述

机器人模型由 Xacro 生成 URDF。TF 描述坐标系关系，例如 `odom -> base_footprint`、`base_link -> lidar_link`。

检查模型：

```bash
xacro src/sentinel_description/urdf/sentinel.urdf.xacro use_sim:=true >/tmp/sentinel.urdf
check_urdf /tmp/sentinel.urdf
```

启动仿真后查看 TF：

```bash
ros2 run tf2_ros tf2_echo odom base_footprint
```

代码位置：

- `src/sentinel_description/urdf/sentinel.urdf.xacro`
- `src/sentinel_description/launch/description.launch.py`

自测：

1. Xacro 相比手写 URDF 的好处是什么？
2. `odom -> base_footprint` 是静态 TF 还是动态 TF？
3. 传感器挂载 frame 为什么重要？

## 7. ros2_control 与仿真

`ros2_control` 把控制器和机器人硬件接口连接起来。在本项目里，Gazebo 通过 `gz_ros2_control` 模拟硬件。

启动带控制器的仿真：

```bash
ros2 launch sentinel_gazebo sim.launch.py headless:=true spawn_controllers:=true
```

检查控制器：

```bash
ros2 control list_controllers
ros2 topic echo /diff_drive_controller/odom --once
```

发送速度：

```bash
ros2 topic pub --once /diff_drive_controller/cmd_vel geometry_msgs/msg/TwistStamped \
  "{header: {frame_id: base_footprint}, twist: {linear: {x: 0.2}, angular: {z: 0.3}}}"
```

代码位置：

- `src/sentinel_control/config/controllers.yaml`
- `src/sentinel_control/launch/control.launch.py`

自测：

1. `diff_drive_controller` 控制哪种机器人？
2. `/diff_drive_controller/odom` 表示什么？
3. 为什么本项目用 `TwistStamped` 而不是只写 `Twist`？

## 8. 导航与 SLAM 入门

SLAM 用传感器建图，Nav2 用地图和目标点做导航。Phase 7 已经放好了 launch 和参数：

- `src/sentinel_bringup/launch/mapping.launch.py`
- `src/sentinel_bringup/launch/nav.launch.py`
- `src/sentinel_bringup/config/slam_toolbox.yaml`
- `src/sentinel_bringup/config/nav2.yaml`

当前 `nexus` 缺少 `slam_toolbox`、`nav2_bringup`、`nav2_msgs`，所以 launch 会清楚报缺依赖：

```bash
ros2 launch sentinel_bringup mapping.launch.py start_sim:=false start_joy:=false
ros2 launch sentinel_bringup nav.launch.py start_sim:=false start_mission:=false
```

自测：

1. SLAM 主要解决什么问题？
2. Nav2 运行为什么需要地图或定位？
3. 当前 Phase 7 为什么叫“配置基线”而不是完整导航闭环？

## 9. 诊断与观测

机器人需要告诉操作者自己是否健康。Phase 9 的 `health_monitor` 发布 `/diagnostics`。

```bash
ros2 launch sentinel_mission diagnostics.launch.py
ros2 topic echo /diagnostics --once
```

常用观测命令：

```bash
ros2 doctor --report
ros2 service info /set_mode --verbose
ros2 topic bw /diagnostics
```

代码位置：

- `src/sentinel_mission/src/health_monitor.py`
- `src/sentinel_mission/test/test_mission_diagnostics_launch.py`

自测：

1. `/diagnostics` 当前包含哪两类状态？
2. `ros2 service info --verbose` 能看到什么？
3. 为什么集成测试要真的启动 launch？

## 10. 怎么读源码

建议按这个顺序读：

1. `docs/PHASE_TESTS.md`：先知道每个 Phase 怎么验证。
2. `README.md`：看当前能跑什么。
3. `src/sentinel_interfaces`：理解项目的语言。
4. `src/sentinel_teleop`：看 topic 和参数。
5. `src/sentinel_mission`：看 lifecycle/service/action/diagnostics。
6. `src/sentinel_perception`：看 component container。
7. `src/sentinel_gazebo` 和 `src/sentinel_control`：看仿真和控制。

自测：

1. 如果你想改手柄按键映射，先看哪个文件？
2. 如果你想新增一个 diagnostic，先看哪个文件？
3. 如果你想新增一个 ROS interface，应该在哪个包里改？

## 11. 小练习：新增一个按键绑定

目标：给 `gamepad_interface` 增加一个保留按钮参数，不要求立刻实现行为。

1. 打开 `src/sentinel_teleop/config/gamepad.yaml`。
2. 新增一行，例如 `waypoint_button: !!int 12`。
3. 在 `src/sentinel_teleop/sentinel_teleop/gamepad_interface.py` 里 declare/get 这个参数。
4. 在测试里加一个断言，确认参数能读取。
5. 运行：

```bash
colcon test --packages-select sentinel_teleop --event-handlers console_direct+
colcon test-result --verbose
```

自测：

1. 为什么新增参数后要加测试？
2. YAML 里的 `!!int` 有什么作用？
3. 如果参数值超出按钮数量，应该在哪里做校验？
