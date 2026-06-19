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

#include "sentinel_mission/mode_manager.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <utility>

namespace sentinel_mission
{
namespace
{
using CallbackReturn =
  rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;
using namespace std::chrono_literals;
}  // namespace

ModeManager::ModeManager(const rclcpp::NodeOptions & options)
: rclcpp_lifecycle::LifecycleNode("mode_manager", options),
  current_mode_(RoverMode::MODE_TELEOP),
  active_(false),
  cancel_patrol_(false)
{
}

ModeManager::~ModeManager()
{
  stop_patrol_thread();
}

CallbackReturn ModeManager::on_configure(const rclcpp_lifecycle::State &)
{
  rclcpp::QoS mode_qos(1);
  mode_qos.reliable();
  mode_qos.transient_local();
  mode_pub_ = this->create_publisher<RoverMode>("rover_mode", mode_qos);
  set_mode_srv_ = this->create_service<SetMode>(
    "set_mode",
    std::bind(&ModeManager::handle_set_mode, this, std::placeholders::_1, std::placeholders::_2));
  mode_request_sub_ = this->create_subscription<RoverMode>(
    "rover_mode_request",
    rclcpp::QoS(10),
    std::bind(&ModeManager::handle_mode_request, this, std::placeholders::_1));
  patrol_server_ = rclcpp_action::create_server<PatrolRoute>(
    shared_from_this(),
    "patrol_route",
    std::bind(&ModeManager::handle_patrol_goal, this, std::placeholders::_1, std::placeholders::_2),
    std::bind(&ModeManager::handle_patrol_cancel, this, std::placeholders::_1),
    std::bind(&ModeManager::handle_patrol_accepted, this, std::placeholders::_1));
  RCLCPP_INFO(get_logger(), "Mode manager configured");
  return CallbackReturn::SUCCESS;
}

CallbackReturn ModeManager::on_activate(const rclcpp_lifecycle::State &)
{
  active_ = true;
  mode_pub_->on_activate();
  publish_mode();
  RCLCPP_INFO(get_logger(), "Mode manager activated");
  return CallbackReturn::SUCCESS;
}

CallbackReturn ModeManager::on_deactivate(const rclcpp_lifecycle::State &)
{
  active_ = false;
  stop_patrol_thread();
  if (mode_pub_) {
    mode_pub_->on_deactivate();
  }
  RCLCPP_INFO(get_logger(), "Mode manager deactivated");
  return CallbackReturn::SUCCESS;
}

CallbackReturn ModeManager::on_cleanup(const rclcpp_lifecycle::State &)
{
  stop_patrol_thread();
  mode_pub_.reset();
  set_mode_srv_.reset();
  mode_request_sub_.reset();
  patrol_server_.reset();
  active_ = false;
  RCLCPP_INFO(get_logger(), "Mode manager cleaned up");
  return CallbackReturn::SUCCESS;
}

rclcpp_action::GoalResponse ModeManager::handle_patrol_goal(
  const rclcpp_action::GoalUUID & uuid,
  std::shared_ptr<const PatrolRoute::Goal> goal)
{
  (void)uuid;
  if (!active_) {
    RCLCPP_WARN(get_logger(), "Rejecting patrol goal while mode manager is inactive");
    return rclcpp_action::GoalResponse::REJECT;
  }
  if (goal->waypoints.empty()) {
    RCLCPP_WARN(get_logger(), "Rejecting patrol goal with no waypoints");
    return rclcpp_action::GoalResponse::REJECT;
  }
  return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
}

rclcpp_action::CancelResponse ModeManager::handle_patrol_cancel(
  const std::shared_ptr<GoalHandlePatrolRoute> goal_handle)
{
  (void)goal_handle;
  cancel_patrol_.store(true);
  set_mode(RoverMode::MODE_TELEOP, "patrol canceled");
  return rclcpp_action::CancelResponse::ACCEPT;
}

void ModeManager::handle_patrol_accepted(std::shared_ptr<GoalHandlePatrolRoute> goal_handle)
{
  stop_patrol_thread();
  cancel_patrol_.store(false);
  set_mode(RoverMode::MODE_PATROL, "patrol goal accepted");
  patrol_thread_ = std::thread(&ModeManager::execute_patrol, this, std::move(goal_handle));
}

void ModeManager::execute_patrol(std::shared_ptr<GoalHandlePatrolRoute> goal_handle)
{
  const auto goal = goal_handle->get_goal();
  auto result = std::make_shared<PatrolRoute::Result>();
  uint32_t completed = 0;

  for (std::size_t index = 0; rclcpp::ok(); ++index) {
    if (index >= goal->waypoints.size()) {
      if (goal->loop_forever) {
        index = 0;
      } else {
        break;
      }
    }

    if (cancel_patrol_.load() || goal_handle->is_canceling()) {
      result->success = false;
      result->waypoints_completed = completed;
      result->message = "Patrol canceled";
      goal_handle->canceled(result);
      return;
    }

    const auto & waypoint = goal->waypoints[index];
    auto feedback = std::make_shared<PatrolRoute::Feedback>();
    feedback->current_index = static_cast<uint32_t>(index);
    feedback->current_waypoint_name = waypoint.name;
    feedback->distance_remaining_m =
      static_cast<float>(std::hypot(waypoint.pose.position.x, waypoint.pose.position.y));
    feedback->estimated_time_remaining.sec =
      static_cast<int32_t>(std::max(1.0F, waypoint.dwell_seconds));
    feedback->estimated_time_remaining.nanosec = 0;
    goal_handle->publish_feedback(feedback);

    const auto dwell_ms = std::chrono::milliseconds(
      static_cast<int64_t>(std::max(0.1F, waypoint.dwell_seconds) * 1000.0F));
    const auto start = std::chrono::steady_clock::now();
    while (std::chrono::steady_clock::now() - start < dwell_ms) {
      if (cancel_patrol_.load() || goal_handle->is_canceling()) {
        result->success = false;
        result->waypoints_completed = completed;
        result->message = "Patrol canceled";
        goal_handle->canceled(result);
        return;
      }
      std::this_thread::sleep_for(50ms);
    }
    ++completed;
  }

  result->success = true;
  result->waypoints_completed = completed;
  result->message = "Patrol route completed in mission-manager simulation mode";
  goal_handle->succeed(result);
  set_mode(RoverMode::MODE_TELEOP, "patrol route completed");
}

void ModeManager::handle_set_mode(
  const std::shared_ptr<SetMode::Request> request,
  std::shared_ptr<SetMode::Response> response)
{
  response->success = set_mode(request->mode, "set_mode service");
  response->message = response->success ? "mode updated" : "invalid mode";
  response->current_mode = make_mode_msg(current_mode_);
}

void ModeManager::handle_mode_request(const RoverMode::SharedPtr msg)
{
  if (!active_) {
    return;
  }
  set_mode(msg->mode, "rover_mode_request topic");
}

bool ModeManager::set_mode(uint8_t mode, const std::string & reason)
{
  if (!valid_mode(mode)) {
    RCLCPP_WARN(get_logger(), "Ignoring invalid mode %u from %s", mode, reason.c_str());
    return false;
  }
  {
    std::lock_guard<std::mutex> lock(mode_mutex_);
    current_mode_ = mode;
  }
  publish_mode();
  RCLCPP_INFO(get_logger(), "Mode set to %s via %s", mode_label(mode).c_str(), reason.c_str());
  return true;
}

ModeManager::RoverMode ModeManager::make_mode_msg(uint8_t mode) const
{
  RoverMode msg;
  msg.mode = mode;
  msg.mode_label = mode_label(mode);
  msg.stamp = get_clock()->now();
  return msg;
}

std::string ModeManager::mode_label(uint8_t mode) const
{
  switch (mode) {
    case RoverMode::MODE_TELEOP:
      return "TELEOP";
    case RoverMode::MODE_MAPPING:
      return "MAPPING";
    case RoverMode::MODE_PATROL:
      return "PATROL";
    case RoverMode::MODE_ESTOP:
      return "ESTOP";
    default:
      return "UNKNOWN";
  }
}

bool ModeManager::valid_mode(uint8_t mode) const
{
  return mode == RoverMode::MODE_TELEOP ||
         mode == RoverMode::MODE_MAPPING ||
         mode == RoverMode::MODE_PATROL ||
         mode == RoverMode::MODE_ESTOP;
}

void ModeManager::publish_mode()
{
  if (!mode_pub_ || !active_) {
    return;
  }
  uint8_t mode;
  {
    std::lock_guard<std::mutex> lock(mode_mutex_);
    mode = current_mode_;
  }
  mode_pub_->publish(make_mode_msg(mode));
}

void ModeManager::stop_patrol_thread()
{
  cancel_patrol_.store(true);
  if (patrol_thread_.joinable()) {
    patrol_thread_.join();
  }
  cancel_patrol_.store(false);
}

}  // namespace sentinel_mission
