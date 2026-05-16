#!/usr/bin/env python3
"""Mission finite-state-machine for the indoor drone demo.

The default sim mode does not connect to PX4, MAVSDK, ROS2, or a real drone.
The mavsdk mode only verifies PX4 SITL connection and basic takeoff/land; it
does not yet fly the room-scanning waypoint mission.
"""

from __future__ import annotations

import argparse
import asyncio
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
        help="Mission backend. sim logs the FSM; mavsdk runs a basic PX4 SITL takeoff/land check.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.25,
        help="Delay in seconds between simulated state transitions.",
    )
    parser.add_argument("--system-address", default="udp://:14540")
    parser.add_argument("--takeoff-altitude", type=float, default=2.0)
    parser.add_argument("--hover-seconds", type=float, default=5.0)
    parser.add_argument("--connection-timeout", type=float, default=30.0)
    return parser.parse_args()


def log_state(state: MissionState, message: str) -> None:
    print(f"[{state.value}] {message}", flush=True)


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


async def wait_for_mavsdk_connection(drone: object, timeout_sec: float) -> None:
    log_state(MissionState.TAKEOFF, f"waiting for PX4 connection, timeout={timeout_sec:.1f}s")

    async def _wait() -> None:
        async for state in drone.core.connection_state():
            print(f"  connection_state: is_connected={state.is_connected}")
            if state.is_connected:
                return

    await asyncio.wait_for(_wait(), timeout=timeout_sec)
    log_state(MissionState.TAKEOFF, "PX4 connection established")


async def wait_for_mavsdk_health(drone: object, timeout_sec: float) -> None:
    log_state(MissionState.TAKEOFF, f"waiting for vehicle health, timeout={timeout_sec:.1f}s")

    async def _wait() -> None:
        async for health in drone.telemetry.health():
            print(
                "  health: "
                f"global={health.is_global_position_ok}, "
                f"local={health.is_local_position_ok}, "
                f"home={health.is_home_position_ok}"
            )
            if health.is_global_position_ok and health.is_local_position_ok and health.is_home_position_ok:
                return

    await asyncio.wait_for(_wait(), timeout=timeout_sec)
    log_state(MissionState.TAKEOFF, "vehicle health checks passed")


async def try_mavsdk_land(drone: object) -> None:
    try:
        log_state(MissionState.LAND, "attempting safety land")
        await drone.action.land()
    except Exception as exc:
        log_state(MissionState.LAND, f"safety land attempt failed: {exc}")


async def run_mavsdk_takeoff_land(args: argparse.Namespace) -> int:
    try:
        from mavsdk import System
    except ImportError as exc:
        print(f"MAVSDK import failed: {exc}")
        print("Install MAVSDK Python or use --mode sim.")
        return 1

    drone = System()

    print("Mission manager mode: mavsdk")
    print("This mode does not run the room waypoint mission yet.")
    print("It only connects to PX4 SITL and performs takeoff/hover/land.")
    print(f"system_address={args.system_address}")
    print(f"takeoff_altitude={args.takeoff_altitude:.1f} m")
    print(f"hover_seconds={args.hover_seconds:.1f} s")
    print()

    try:
        log_state(MissionState.TAKEOFF, "creating MAVSDK connection")
        await asyncio.wait_for(drone.connect(system_address=args.system_address), timeout=args.connection_timeout)
        await wait_for_mavsdk_connection(drone, args.connection_timeout)
        await wait_for_mavsdk_health(drone, args.connection_timeout)

        log_state(MissionState.TAKEOFF, f"setting takeoff altitude to {args.takeoff_altitude:.1f} m")
        await drone.action.set_takeoff_altitude(args.takeoff_altitude)

        log_state(MissionState.TAKEOFF, "arming")
        await drone.action.arm()

        log_state(MissionState.TAKEOFF, "takeoff command sent")
        await drone.action.takeoff()

        log_state(MissionState.TAKEOFF, f"hovering for {args.hover_seconds:.1f} seconds")
        await asyncio.sleep(args.hover_seconds)

        log_state(MissionState.LAND, "land command sent")
        await drone.action.land()

        log_state(MissionState.FINISH, "MAVSDK takeoff/land mission complete")
        return 0

    except asyncio.TimeoutError:
        print("Timed out while waiting for PX4 connection or vehicle health.")
        print("Make sure PX4 SITL is running and MAVLink is available on udp://:14540.")
        await try_mavsdk_land(drone)
        return 1
    except Exception as exc:
        print(f"MAVSDK mission failed: {exc}")
        await try_mavsdk_land(drone)
        return 1


def main() -> int:
    args = parse_args()
    if args.mode == "sim":
        run_simulated_mission(args.sleep)
        return 0
    return asyncio.run(run_mavsdk_takeoff_land(args))


if __name__ == "__main__":
    raise SystemExit(main())
