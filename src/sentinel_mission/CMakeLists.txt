cmake_minimum_required(VERSION 3.20)
project(sentinel_mission)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)
find_package(sentinel_interfaces REQUIRED)

add_executable(mode_manager
  src/mode_manager.cpp
  src/mode_manager_main.cpp
)
target_compile_features(mode_manager PUBLIC cxx_std_17)
target_include_directories(mode_manager PUBLIC
  "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
  "$<INSTALL_INTERFACE:include>"
)
target_link_libraries(mode_manager
  rclcpp::rclcpp
  rclcpp_action::rclcpp_action
  rclcpp_lifecycle::rclcpp_lifecycle
  sentinel_interfaces::sentinel_interfaces
)

install(TARGETS
  mode_manager
  DESTINATION lib/${PROJECT_NAME}
)

install(PROGRAMS
  src/health_monitor.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME health_monitor
)

install(PROGRAMS
  src/mission_logger.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME mission_logger
)

install(
  DIRECTORY
    config
    launch
    resource
    include
  DESTINATION share/${PROJECT_NAME}
  OPTIONAL
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
  find_package(launch_testing_ament_cmake REQUIRED)
  add_launch_test(test/test_mission_diagnostics_launch.py TIMEOUT 30)
endif()

ament_package()
