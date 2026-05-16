#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[indoor_drone_gas_demo] Project directory: ${PROJECT_DIR}"
echo "[indoor_drone_gas_demo] This is a first-stage launcher placeholder."
echo
echo "Planned startup sequence:"
echo "  1. Source ROS2 Humble environment"
echo "  2. Start PX4 SITL"
echo "  3. Launch Gazebo Classic with worlds/simple_corridor_room.world"
echo "  4. Start ROS2 demo launch file"
echo "  5. Start MAVSDK mission manager"
echo

if command -v ros2 >/dev/null 2>&1; then
  echo "ros2 found: $(command -v ros2)"
else
  echo "ros2 not found in PATH. Source ROS2 Humble before running the full demo."
fi

if command -v gazebo >/dev/null 2>&1; then
  echo "gazebo found: $(command -v gazebo)"
else
  echo "gazebo not found in PATH. Install/source Gazebo Classic before running the full demo."
fi

echo
echo "Next implementation step:"
echo "  ros2 launch indoor_drone_gas_demo demo.launch.py"
