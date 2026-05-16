#!/usr/bin/env python3
"""Simulated mission finite-state-machine for the indoor drone demo.

This script does not connect to PX4, MAVSDK, ROS2, or a real drone. It only
prints the planned mission flow so the task logic can be reviewed safely before
flight-stack integration.

TODO: Add --mode mavsdk and send real commands through MAVSDK after SITL is
stable.
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from enum import Enum


class MissionState(str, Enum):
    TAKEOFF = "TAKEOFF"
    ENTER_ENVIRONMENT = "ENTER_ENVIRONMENT"
    EXPLORE_CORRIDOR = "EXPLORE_CORRIDOR"
    ENTER_ROOM = "ENTER_ROOM"
    SAMPLE_GAS = "SAMPLE_GAS"
    MAP_UPDATE = "MAP_UPDATE"
    RETURN_TO_SAFE_EXIT = "RETURN_TO_SAFE_EXIT"
    LAND = "LAND"
    FINISH = "FINISH"


@dataclass(frozen=True)
class Waypoint:
    name: str
    x: float
    y: float
    z: float
    sample: bool = False
    room: bool = False


MISSION_WAYPOINTS: list[Waypoint] = [
    Waypoint("START_SAFE_EXIT", 0.0, 0.0, 1.5),
    Waypoint("CORRIDOR_ENTRY", 2.0, 0.0, 1.5, sample=True),
    Waypoint("LEFT_ROOM", 5.0, 4.0, 1.5, sample=True, room=True),
    Waypoint("CORRIDOR_MID", 7.0, 0.0, 1.5, sample=True),
    Waypoint("RIGHT_ROOM", 9.0, -4.0, 1.5, sample=True, room=True),
    Waypoint("FORWARD_ROOM", 13.0, 3.0, 1.5, sample=True, room=True),
    Waypoint("RETURN_CORRIDOR", 7.0, 0.0, 1.5, sample=True),
    Waypoint("START_SAFE_EXIT_RETURN", 0.0, 0.0, 1.5),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the simulated mission FSM.")
    parser.add_argument(
        "--mode",
        default="sim",
        choices=["sim", "mavsdk"],
        help="Mission backend. Only sim is implemented in this stage.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.25,
        help="Delay in seconds between simulated state transitions.",
    )
    return parser.parse_args()


def log_state(state: MissionState, message: str) -> None:
    print(f"[{state.value}] {message}")


def log_waypoint(prefix: str, waypoint: Waypoint) -> None:
    print(f"  {prefix}: {waypoint.name} -> x={waypoint.x:.1f}, y={waypoint.y:.1f}, z={waypoint.z:.1f}")


def pause(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)


def sample_and_update(waypoint: Waypoint, sleep_seconds: float) -> None:
    log_state(MissionState.SAMPLE_GAS, f"gas sample requested at {waypoint.name}")
    log_waypoint("sample position", waypoint)
    pause(sleep_seconds)

    log_state(MissionState.MAP_UPDATE, f"map update triggered after sampling {waypoint.name}")
    pause(sleep_seconds)


def run_simulated_mission(sleep_seconds: float) -> None:
    print("Mission manager mode: sim")
    print("No PX4, MAVSDK, ROS2, or real drone commands are used in this mode.")
    print()

    start = MISSION_WAYPOINTS[0]
    corridor_entry = MISSION_WAYPOINTS[1]
    return_corridor = MISSION_WAYPOINTS[-2]
    safe_exit_return = MISSION_WAYPOINTS[-1]

    log_state(MissionState.TAKEOFF, "arming/checks would happen here in future MAVSDK mode")
    log_waypoint("takeoff target", start)
    pause(sleep_seconds)

    log_state(MissionState.ENTER_ENVIRONMENT, "entering the indoor environment from START / SAFE_EXIT")
    log_waypoint("target", corridor_entry)
    pause(sleep_seconds)
    sample_and_update(corridor_entry, sleep_seconds)

    for waypoint in MISSION_WAYPOINTS[2:6]:
        log_state(MissionState.EXPLORE_CORRIDOR, f"navigating corridor toward {waypoint.name}")
        log_waypoint("target", waypoint)
        pause(sleep_seconds)

        if waypoint.room:
            log_state(MissionState.ENTER_ROOM, f"entering room/area: {waypoint.name}")
            log_waypoint("room scan target", waypoint)
            pause(sleep_seconds)

        if waypoint.sample:
            sample_and_update(waypoint, sleep_seconds)

    log_state(MissionState.EXPLORE_CORRIDOR, "returning to the main corridor after room visits")
    log_waypoint("target", return_corridor)
    pause(sleep_seconds)
    sample_and_update(return_corridor, sleep_seconds)

    log_state(MissionState.RETURN_TO_SAFE_EXIT, "return route: RETURN_CORRIDOR -> START_SAFE_EXIT_RETURN")
    log_waypoint("return start", return_corridor)
    log_waypoint("return target", safe_exit_return)
    pause(sleep_seconds)

    log_state(MissionState.LAND, "landing at START / SAFE_EXIT; no separate corridor-end landing area is used")
    log_waypoint("landing position", safe_exit_return)
    pause(sleep_seconds)

    log_state(MissionState.FINISH, "simulated mission complete")


def main() -> int:
    args = parse_args()
    if args.mode != "sim":
        print("--mode mavsdk is reserved for a later stage. No MAVSDK integration is implemented yet.")
        return 2

    run_simulated_mission(args.sleep)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
