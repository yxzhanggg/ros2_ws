cmake_minimum_required(VERSION 3.20)
project(sentinel_perception)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY
    config
    launch
    resource
    src
    include
  DESTINATION share/${PROJECT_NAME}
  OPTIONAL
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
