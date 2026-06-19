cmake_minimum_required(VERSION 3.20)
project(sentinel_perception)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)

add_library(sentinel_perception_components SHARED
  src/image_marker_component.cpp
  src/scan_filter_component.cpp
)
target_compile_features(sentinel_perception_components PUBLIC cxx_std_17)
target_include_directories(sentinel_perception_components PUBLIC
  "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>"
  "$<INSTALL_INTERFACE:include>"
)
target_link_libraries(sentinel_perception_components
  rclcpp::rclcpp
  rclcpp_components::component
  sensor_msgs::sensor_msgs__rosidl_typesupport_cpp
  std_msgs::std_msgs__rosidl_typesupport_cpp
)

rclcpp_components_register_nodes(
  sentinel_perception_components
  "sentinel_perception::ImageMarkerComponent"
  "sentinel_perception::ScanFilterComponent"
)

install(TARGETS
  sentinel_perception_components
  EXPORT export_sentinel_perception_components
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
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

install(DIRECTORY include/
  DESTINATION include
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_export_include_directories(include)
ament_export_libraries(sentinel_perception_components)
ament_export_targets(export_sentinel_perception_components)
ament_export_dependencies(rclcpp rclcpp_components sensor_msgs std_msgs)

ament_package()
