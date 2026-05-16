#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PX4_DIR="/home/sefa/src/PX4-Autopilot"
WORLD_FILE="${PROJECT_DIR}/worlds/simple_corridor_room.world"
HEADLESS_MODE=0
CLEAN_FIRST=0
VERBOSE_SIM_MODE=0

usage() {
  cat <<EOF
Usage: ./scripts/start_px4_custom_world.sh [options]

Options:
  --clean              Kill old PX4/Gazebo processes and remove Gazebo server/client cache.
  --headless           Start gzserver only. Do not start Gazebo GUI.
  --px4-dir PATH       PX4-Autopilot directory. Default: ${PX4_DIR}
  --world PATH         Gazebo Classic world file. Default: ${WORLD_FILE}
  --verbose            Enable verbose Gazebo simulator logs.
  -h, --help           Show this help.

Examples:
  ./scripts/start_px4_custom_world.sh --clean
  ./scripts/start_px4_custom_world.sh --clean --headless
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --clean)
      CLEAN_FIRST=1
      shift
      ;;
    --headless)
      HEADLESS_MODE=1
      shift
      ;;
    --px4-dir)
      PX4_DIR="${2:-}"
      shift 2
      ;;
    --world)
      WORLD_FILE="${2:-}"
      shift 2
      ;;
    --verbose)
      VERBOSE_SIM_MODE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      usage
      exit 2
      ;;
  esac
done

PX4_DIR="$(realpath "${PX4_DIR}")"
WORLD_FILE="$(realpath "${WORLD_FILE}")"
PX4_BUILD_DIR="${PX4_DIR}/build/px4_sitl_default"
PX4_SITL_BIN="${PX4_BUILD_DIR}/bin/px4"
SITL_RUN="${PX4_DIR}/Tools/simulation/gazebo-classic/sitl_run.sh"
GAZEBO_SETUP="${PX4_DIR}/Tools/simulation/gazebo-classic/setup_gazebo.bash"

if [[ ! -d "${PX4_DIR}" ]]; then
  echo "PX4 directory not found: ${PX4_DIR}"
  exit 1
fi

if [[ ! -f "${WORLD_FILE}" ]]; then
  echo "World file not found: ${WORLD_FILE}"
  exit 1
fi

if [[ ! -x "${PX4_SITL_BIN}" ]]; then
  echo "PX4 SITL binary not found or not executable: ${PX4_SITL_BIN}"
  echo "Build PX4 SITL first, for example:"
  echo "  cd ${PX4_DIR}"
  echo "  HEADLESS=1 PX4_SIM_MODEL=iris make px4_sitl gazebo-classic"
  exit 1
fi

if [[ ! -x "${SITL_RUN}" ]]; then
  echo "PX4 sitl_run.sh not found or not executable: ${SITL_RUN}"
  exit 1
fi

if [[ ! -f "${GAZEBO_SETUP}" ]]; then
  echo "PX4 Gazebo setup file not found: ${GAZEBO_SETUP}"
  exit 1
fi

if [[ "${CLEAN_FIRST}" -eq 1 ]]; then
  echo "[clean] Stopping old PX4/Gazebo processes if any"
  pkill -9 -x px4 || true
  pkill -9 -x gzserver || true
  pkill -9 -x gzclient || true
  pkill -9 -x gazebo || true
  pkill -9 -f "${SITL_RUN}" || true

  echo "[clean] Removing Gazebo server/client cache"
  rm -rf "${HOME}/.gazebo/server-"* "${HOME}/.gazebo/client-"*
  mkdir -p "${HOME}/.gazebo"
  chmod 755 "${HOME}/.gazebo" || true
fi

export GAZEBO_PLUGIN_PATH="${GAZEBO_PLUGIN_PATH:-}"
export GAZEBO_MODEL_PATH="${GAZEBO_MODEL_PATH:-}"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"

# shellcheck source=/dev/null
source "${GAZEBO_SETUP}" "${PX4_DIR}" "${PX4_BUILD_DIR}"

export PX4_SIM_MODEL="iris"
export PX4_SITL_WORLD="${WORLD_FILE}"

if [[ "${HEADLESS_MODE}" -eq 1 ]]; then
  export HEADLESS=1
else
  unset HEADLESS || true
fi

if [[ "${VERBOSE_SIM_MODE}" -eq 1 ]]; then
  export VERBOSE_SIM=1
fi

echo "[indoor_drone_gas_demo] PX4 custom world startup"
echo "Project directory: ${PROJECT_DIR}"
echo "PX4 directory: ${PX4_DIR}"
echo "World file: ${WORLD_FILE}"
echo "Mode: $([[ "${HEADLESS_MODE}" -eq 1 ]] && echo headless || echo gui)"
echo
echo "Environment:"
echo "  PX4_SIM_MODEL=${PX4_SIM_MODEL}"
echo "  PX4_SITL_WORLD=${PX4_SITL_WORLD}"
echo "  GAZEBO_PLUGIN_PATH=${GAZEBO_PLUGIN_PATH:-}"
echo "  GAZEBO_MODEL_PATH=${GAZEBO_MODEL_PATH:-}"
echo "  LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-}"
echo
echo "Command:"
echo "  ${SITL_RUN} ${PX4_SITL_BIN} none iris none ${PX4_DIR} ${PX4_BUILD_DIR}"
echo
echo "Expected result:"
echo "  Gazebo Classic opens ${WORLD_FILE}"
echo "  PX4 spawns iris in the custom world"
echo "  PX4 eventually prints a ready/takeoff-ready status"
echo

exec "${SITL_RUN}" "${PX4_SITL_BIN}" none iris none "${PX4_DIR}" "${PX4_BUILD_DIR}"
