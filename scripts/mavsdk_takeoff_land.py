#!/usr/bin/env python3
"""Minimal MAVSDK takeoff/land connection test for PX4 SITL.

This script does not start PX4, Gazebo, or ROS2. Start PX4 SITL separately,
then run this script to verify MAVSDK can connect, arm, take off, hover, and
land.
"""

from __future__ import annotations

import argparse
import asyncio

from mavsdk import System


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MAVSDK PX4 SITL takeoff/land smoke test.")
    parser.add_argument("--system-address", default="udp://:14540")
    parser.add_argument("--takeoff-altitude", type=float, default=2.0)
    parser.add_argument("--hover-seconds", type=float, default=5.0)
    parser.add_argument("--connection-timeout", type=float, default=30.0)
    return parser.parse_args()


async def wait_for_connection(drone: System, timeout_sec: float) -> None:
    print(f"[connect] Waiting for PX4 connection, timeout={timeout_sec:.1f}s")

    async def _wait() -> None:
        async for state in drone.core.connection_state():
            print(f"[connect] is_connected={state.is_connected}")
            if state.is_connected:
                return

    await asyncio.wait_for(_wait(), timeout=timeout_sec)
    print("[connect] Connected")


async def wait_for_health(drone: System, timeout_sec: float) -> None:
    print(f"[health] Waiting for global/local position and home position, timeout={timeout_sec:.1f}s")

    async def _wait() -> None:
        async for health in drone.telemetry.health():
            print(
                "[health] "
                f"global={health.is_global_position_ok}, "
                f"local={health.is_local_position_ok}, "
                f"home={health.is_home_position_ok}"
            )
            if health.is_global_position_ok and health.is_local_position_ok and health.is_home_position_ok:
                return

    await asyncio.wait_for(_wait(), timeout=timeout_sec)
    print("[health] Health checks passed")


async def try_land(drone: System) -> None:
    try:
        print("[safety] Attempting land")
        await drone.action.land()
    except Exception as exc:
        print(f"[safety] Land attempt failed: {exc}")


async def run() -> int:
    args = parse_args()
    drone = System()

    print("[mavsdk_takeoff_land] PX4 SITL MAVSDK smoke test")
    print(f"[config] system_address={args.system_address}")
    print(f"[config] takeoff_altitude={args.takeoff_altitude:.1f} m")
    print(f"[config] hover_seconds={args.hover_seconds:.1f} s")
    print()

    try:
        print("[connect] Creating MAVSDK connection")
        await drone.connect(system_address=args.system_address)
        await wait_for_connection(drone, args.connection_timeout)
        await wait_for_health(drone, args.connection_timeout)

        print(f"[action] Setting takeoff altitude to {args.takeoff_altitude:.1f} m")
        await drone.action.set_takeoff_altitude(args.takeoff_altitude)

        print("[action] Arming")
        await drone.action.arm()

        print("[action] Takeoff")
        await drone.action.takeoff()

        print(f"[action] Hovering for {args.hover_seconds:.1f} seconds")
        await asyncio.sleep(args.hover_seconds)

        print("[action] Landing")
        await drone.action.land()

        print("[done] Land command sent. Test complete.")
        return 0

    except asyncio.TimeoutError:
        print("[error] Timed out while waiting for connection or vehicle health.")
        print("[hint] Make sure PX4 SITL is running and MAVLink is available on udp://:14540.")
        await try_land(drone)
        return 1
    except Exception as exc:
        print(f"[error] MAVSDK takeoff/land test failed: {exc}")
        await try_land(drone)
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
