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

#include "sentinel_perception/image_marker_component.hpp"

#include <algorithm>
#include <cstdint>
#include <iomanip>
#include <memory>
#include <sstream>
#include <string>

#include "rclcpp_components/register_node_macro.hpp"

namespace sentinel_perception
{

ImageMarkerComponent::ImageMarkerComponent(const rclcpp::NodeOptions & options)
: rclcpp::Node("image_marker_detector", options)
{
  bright_threshold_ = declare_parameter<double>("bright_threshold", 180.0);
  const auto stride_param = declare_parameter<int>("sample_stride", 4);
  sample_stride_ = static_cast<std::size_t>(std::max(1L, stride_param));

  detection_pub_ = create_publisher<std_msgs::msg::String>("detections", rclcpp::QoS(10));
  image_sub_ = create_subscription<sensor_msgs::msg::Image>(
    "camera/image",
    rclcpp::SensorDataQoS(),
    std::bind(&ImageMarkerComponent::handle_image, this, std::placeholders::_1));
}

void ImageMarkerComponent::handle_image(sensor_msgs::msg::Image::UniquePtr image)
{
  if (image->data.empty()) {
    return;
  }

  std::uint64_t sum = 0;
  std::size_t samples = 0;
  for (std::size_t index = 0; index < image->data.size(); index += sample_stride_) {
    sum += image->data[index];
    ++samples;
  }
  if (samples == 0) {
    return;
  }

  const double mean_brightness = static_cast<double>(sum) / static_cast<double>(samples);
  const bool bright_marker = mean_brightness >= bright_threshold_;

  std_msgs::msg::String detection;
  std::ostringstream out;
  out << std::fixed << std::setprecision(2)
      << "{\"frame_id\":\"" << image->header.frame_id
      << "\",\"width\":" << image->width
      << ",\"height\":" << image->height
      << ",\"mean_brightness\":" << mean_brightness
      << ",\"bright_marker\":" << (bright_marker ? "true" : "false")
      << "}";
  detection.data = out.str();
  detection_pub_->publish(detection);
}

}  // namespace sentinel_perception

RCLCPP_COMPONENTS_REGISTER_NODE(sentinel_perception::ImageMarkerComponent)
