cmake_minimum_required(VERSION 3.20)
project(sentinel_interfaces)

find_package(ament_cmake REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/RoverMode.msg"
  "msg/Waypoint.msg"
  "srv/SetMode.srv"
  "action/PatrolRoute.action"
  DEPENDENCIES builtin_interfaces geometry_msgs
)

install(
  DIRECTORY
    action
    config
    launch
    msg
    resource
    srv
  DESTINATION share/${PROJECT_NAME}
  OPTIONAL
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_export_dependencies(rosidl_default_runtime)
ament_package()
