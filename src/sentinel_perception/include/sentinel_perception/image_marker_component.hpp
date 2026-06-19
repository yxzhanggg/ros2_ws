// Copyright 2026 yxzhanggg
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef SENTINEL_PERCEPTION__IMAGE_MARKER_COMPONENT_HPP_
#define SENTINEL_PERCEPTION__IMAGE_MARKER_COMPONENT_HPP_

#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "std_msgs/msg/string.hpp"

namespace sentinel_perception
{

class ImageMarkerComponent : public rclcpp::Node
{
public:
  explicit ImageMarkerComponent(const rclcpp::NodeOptions & options);

private:
  void handle_image(sensor_msgs::msg::Image::UniquePtr image);

  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr image_sub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr detection_pub_;
  double bright_threshold_;
  std::size_t sample_stride_;
};

}  // namespace sentinel_perception

#endif  // SENTINEL_PERCEPTION__IMAGE_MARKER_COMPONENT_HPP_
