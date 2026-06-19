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

#include "sentinel_perception/scan_filter_component.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <memory>

#include "rclcpp_components/register_node_macro.hpp"

namespace sentinel_perception
{

ScanFilterComponent::ScanFilterComponent(const rclcpp::NodeOptions & options)
: rclcpp::Node("scan_filter", options)
{
  min_range_m_ = declare_parameter<double>("min_range_m", 0.08);
  max_range_m_ = declare_parameter<double>("max_range_m", 12.0);
  replace_invalid_with_max_ = declare_parameter<bool>("replace_invalid_with_max", true);

  scan_pub_ = create_publisher<sensor_msgs::msg::LaserScan>(
    "scan_filtered",
    rclcpp::SensorDataQoS());
  scan_sub_ = create_subscription<sensor_msgs::msg::LaserScan>(
    "scan",
    rclcpp::SensorDataQoS(),
    std::bind(&ScanFilterComponent::handle_scan, this, std::placeholders::_1));
}

void ScanFilterComponent::handle_scan(sensor_msgs::msg::LaserScan::UniquePtr scan)
{
  const auto min_range = static_cast<float>(std::max(0.0, min_range_m_));
  const auto max_range = static_cast<float>(std::max(min_range_m_, max_range_m_));
  scan->range_min = std::max(scan->range_min, min_range);
  scan->range_max = std::min(scan->range_max, max_range);

  for (auto & range : scan->ranges) {
    const auto bounded_range = std::clamp(range, min_range, max_range);
    const bool out_of_bounds = bounded_range != range;
    const bool invalid = !std::isfinite(range) || out_of_bounds;
    if (invalid) {
      range = replace_invalid_with_max_ ? max_range : std::numeric_limits<float>::quiet_NaN();
    }
  }

  scan_pub_->publish(std::move(scan));
}

}  // namespace sentinel_perception

RCLCPP_COMPONENTS_REGISTER_NODE(sentinel_perception::ScanFilterComponent)
