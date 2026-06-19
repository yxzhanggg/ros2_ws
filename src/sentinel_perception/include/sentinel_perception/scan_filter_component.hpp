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

#ifndef SENTINEL_PERCEPTION__SCAN_FILTER_COMPONENT_HPP_
#define SENTINEL_PERCEPTION__SCAN_FILTER_COMPONENT_HPP_

#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"

namespace sentinel_perception
{

class ScanFilterComponent : public rclcpp::Node
{
public:
  explicit ScanFilterComponent(const rclcpp::NodeOptions & options);

private:
  void handle_scan(sensor_msgs::msg::LaserScan::UniquePtr scan);

  rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr scan_sub_;
  rclcpp::Publisher<sensor_msgs::msg::LaserScan>::SharedPtr scan_pub_;
  double min_range_m_;
  double max_range_m_;
  bool replace_invalid_with_max_;
};

}  // namespace sentinel_perception

#endif  // SENTINEL_PERCEPTION__SCAN_FILTER_COMPONENT_HPP_
