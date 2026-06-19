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

#ifndef SENTINEL_MISSION__MODE_MANAGER_HPP_
#define SENTINEL_MISSION__MODE_MANAGER_HPP_

#include <atomic>
#include <memory>
#include <mutex>
#include <string>
#include <thread>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "rclcpp_lifecycle/lifecycle_node.hpp"
#include "sentinel_interfaces/action/patrol_route.hpp"
#include "sentinel_interfaces/msg/rover_mode.hpp"
#include "sentinel_interfaces/srv/set_mode.hpp"

namespace sentinel_mission
{

class ModeManager : public rclcpp_lifecycle::LifecycleNode
{
public:
  using RoverMode = sentinel_interfaces::msg::RoverMode;
  using SetMode = sentinel_interfaces::srv::SetMode;
  using PatrolRoute = sentinel_interfaces::action::PatrolRoute;
  using GoalHandlePatrolRoute = rclcpp_action::ServerGoalHandle<PatrolRoute>;

  explicit ModeManager(const rclcpp::NodeOptions & options = rclcpp::NodeOptions());
  ~ModeManager() override;

protected:
  rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn
  on_configure(const rclcpp_lifecycle::State & state) override;

  rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn
  on_activate(const rclcpp_lifecycle::State & state) override;

  rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn
  on_deactivate(const rclcpp_lifecycle::State & state) override;

  rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn
  on_cleanup(const rclcpp_lifecycle::State & state) override;

private:
  rclcpp_action::GoalResponse handle_patrol_goal(
    const rclcpp_action::GoalUUID & uuid,
    std::shared_ptr<const PatrolRoute::Goal> goal);
  rclcpp_action::CancelResponse handle_patrol_cancel(
    const std::shared_ptr<GoalHandlePatrolRoute> goal_handle);
  void handle_patrol_accepted(std::shared_ptr<GoalHandlePatrolRoute> goal_handle);
  void execute_patrol(std::shared_ptr<GoalHandlePatrolRoute> goal_handle);

  void handle_set_mode(
    const std::shared_ptr<SetMode::Request> request,
    std::shared_ptr<SetMode::Response> response);
  void handle_mode_request(const RoverMode::SharedPtr msg);
  bool set_mode(uint8_t mode, const std::string & reason);
  RoverMode make_mode_msg(uint8_t mode) const;
  std::string mode_label(uint8_t mode) const;
  bool valid_mode(uint8_t mode) const;
  void publish_mode();
  void stop_patrol_thread();

  rclcpp_lifecycle::LifecyclePublisher<RoverMode>::SharedPtr mode_pub_;
  rclcpp::Service<SetMode>::SharedPtr set_mode_srv_;
  rclcpp::Subscription<RoverMode>::SharedPtr mode_request_sub_;
  rclcpp_action::Server<PatrolRoute>::SharedPtr patrol_server_;

  mutable std::mutex mode_mutex_;
  uint8_t current_mode_;
  bool active_;
  std::atomic_bool cancel_patrol_;
  std::thread patrol_thread_;
};

}  // namespace sentinel_mission

#endif  // SENTINEL_MISSION__MODE_MANAGER_HPP_
