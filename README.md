# Nexus Sentinel ROS 2 Workspace

Nexus Sentinel is a ROS 2 simulation workspace for a warehouse and campus inspection robot. The robot is intended to support autonomous patrol, mapping, operator teleoperation with a PS5 DualSense controller, and later safety/diagnostic workflows.

## Current Phase

Phase 1 is complete: the workspace contains the package skeletons for the project architecture. Functional robot interfaces, simulation assets, controllers, teleoperation, mission logic, navigation, perception, and documentation will be implemented in later phases.

## Workspace Layout

```text
ros2_ws/
├── src/
│   ├── sentinel_interfaces/
│   ├── sentinel_description/
│   ├── sentinel_gazebo/
│   ├── sentinel_control/
│   ├── sentinel_teleop/
│   ├── sentinel_mission/
│   ├── sentinel_perception/
│   └── sentinel_bringup/
├── docs/
│   ├── CHANGELOG.md
│   └── DEPENDENCIES.md
└── README.md
```

## Build And Test

On `nexus`:

```bash
cd ~/ros2_ws
source /opt/ros/lyrical/setup.bash
colcon build
colcon test
colcon test-result --verbose
```

Phase 1 verification result: 8 packages built successfully; 40 tests ran with 0 errors, 0 failures, and 1 skipped template copyright test.
