from __future__ import annotations

import json
import platform
import shutil
import socket
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

import psutil


def _run_command(command: list[str], *, timeout: float = 5.0) -> str | None:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (FileNotFoundError, subprocess.SubprocessError, PermissionError, OSError):
        return None

    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_psutil(callable_obj, default):
    try:
        return callable_obj()
    except (psutil.Error, PermissionError, OSError):
        return default


def get_cpu_status() -> dict[str, Any]:
    load_avg = os_load_average()
    return {
        "physical_cores": _safe_psutil(lambda: psutil.cpu_count(logical=False), None),
        "logical_cores": _safe_psutil(lambda: psutil.cpu_count(logical=True), None),
        "usage_percent": _safe_psutil(lambda: psutil.cpu_percent(interval=0.3), None),
        "load_average": load_avg,
        "frequency_mhz": _cpu_frequency(),
    }


def get_memory_status() -> dict[str, Any]:
    memory = _safe_psutil(psutil.virtual_memory, None)
    swap = _safe_psutil(psutil.swap_memory, None)
    if memory is None or swap is None:
        return {
            "available": False,
            "note": "Memory metrics are unavailable in the current execution context.",
        }
    return {
        "total_bytes": memory.total,
        "available_bytes": memory.available,
        "used_bytes": memory.used,
        "usage_percent": memory.percent,
        "swap_total_bytes": swap.total,
        "swap_used_bytes": swap.used,
        "swap_usage_percent": swap.percent,
    }


def get_disk_status() -> dict[str, Any]:
    usage = shutil.disk_usage("/")
    return {
        "path": "/",
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "usage_percent": round((usage.used / usage.total) * 100, 2) if usage.total else 0,
    }


def get_battery_status() -> dict[str, Any]:
    battery = _safe_psutil(psutil.sensors_battery, None)
    if battery is not None:
        return {
            "available": True,
            "percent": battery.percent,
            "power_plugged": battery.power_plugged,
            "seconds_left": battery.secsleft,
        }

    raw = _run_command(["pmset", "-g", "batt"])
    return {
        "available": raw is not None,
        "raw": raw,
    }


def get_network_status() -> dict[str, Any]:
    io = _safe_psutil(psutil.net_io_counters, None)
    if io is None:
        return {
            "available": False,
            "note": "Network metrics are unavailable in the current execution context.",
        }

    addresses = []
    interface_map = _safe_psutil(psutil.net_if_addrs, {})
    for interface, values in interface_map.items():
        for value in values:
            if value.family == socket.AF_INET:
                addresses.append(
                    {
                        "interface": interface,
                        "family": "ipv4",
                        "address": value.address,
                    }
                )

    return {
        "bytes_sent": io.bytes_sent,
        "bytes_recv": io.bytes_recv,
        "packets_sent": io.packets_sent,
        "packets_recv": io.packets_recv,
        "addresses": addresses,
    }


def get_top_processes(*, limit: int = 5, sort_by: str = "cpu") -> list[dict[str, Any]]:
    sort_field = "memory_percent" if sort_by == "memory" else "cpu_percent"

    processes = []
    try:
        for process in psutil.process_iter(
            ["pid", "name", "username", "cpu_percent", "memory_percent", "status"]
        ):
            try:
                info = process.info
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
            info["cpu_percent"] = _metric_value(info.get("cpu_percent"))
            info["memory_percent"] = _metric_value(info.get("memory_percent"))
            processes.append(info)
    except (psutil.Error, PermissionError, OSError):
        fallback = _top_processes_fallback(limit=limit, sort_by=sort_by)
        return fallback

    processes.sort(key=lambda item: _metric_value(item.get(sort_field)), reverse=True)
    return processes[: max(1, min(limit, 25))]


def get_gpu_status() -> dict[str, Any]:
    raw_json = _run_command(["system_profiler", "SPDisplaysDataType", "-json"], timeout=15.0)
    if not raw_json:
        return {
            "available": False,
            "note": "GPU usage metrics are not available. This endpoint currently exposes GPU hardware info only.",
        }

    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError:
        return {
            "available": False,
            "note": "Unable to parse GPU information from system_profiler.",
        }

    items = parsed.get("SPDisplaysDataType", [])
    normalized = []
    for item in items:
        normalized.append(
            {
                "model": item.get("sppci_model"),
                "vendor": item.get("spdisplays_vendor"),
                "metal_support": item.get("spdisplays_metal"),
                "vram": item.get("spdisplays_vram") or item.get("spdisplays_vram_shared"),
            }
        )

    return {
        "available": bool(normalized),
        "devices": normalized,
        "note": "macOS does not expose lightweight GPU utilization metrics consistently without elevated tooling.",
    }


def get_system_status() -> dict[str, Any]:
    raw_boot_time = _safe_psutil(psutil.boot_time, None)
    boot_time = (
        datetime.fromtimestamp(raw_boot_time, tz=timezone.utc).isoformat()
        if raw_boot_time is not None
        else None
    )
    uptime_seconds = int(time.time() - raw_boot_time) if raw_boot_time is not None else None
    return {
        "timestamp": iso_now(),
        "hostname": socket.gethostname(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "uptime_seconds": uptime_seconds,
        "boot_time": boot_time,
        "cpu": get_cpu_status(),
        "memory": get_memory_status(),
        "disk": get_disk_status(),
        "battery": get_battery_status(),
        "network": get_network_status(),
        "gpu": get_gpu_status(),
    }


def os_load_average() -> dict[str, float] | None:
    if hasattr(psutil, "getloadavg"):
        values = _safe_psutil(psutil.getloadavg, None)
        if values is None:
            return None
        one, five, fifteen = values
        return {"1m": one, "5m": five, "15m": fifteen}
    return None


def _cpu_frequency() -> float | None:
    frequency = _safe_psutil(psutil.cpu_freq, None)
    if frequency is None:
        return None
    return frequency.current


def _metric_value(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _top_processes_fallback(*, limit: int, sort_by: str) -> list[dict[str, Any]]:
    if sort_by == "memory":
        command = ["ps", "-arcxo", "pid=,comm=,%mem=,%cpu=,state="]
    else:
        command = ["ps", "-arcxo", "pid=,comm=,%cpu=,%mem=,state="]

    output = _run_command(command)
    if not output:
        return []

    rows = []
    for line in output.splitlines()[: max(1, min(limit, 25))]:
        parts = line.split(None, 4)
        if len(parts) != 5:
            continue
        pid, name, first_metric, second_metric, status = parts
        if sort_by == "memory":
            memory_percent = float(first_metric)
            cpu_percent = float(second_metric)
        else:
            cpu_percent = float(first_metric)
            memory_percent = float(second_metric)
        rows.append(
            {
                "pid": int(pid),
                "name": name,
                "username": None,
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "status": status,
            }
        )
    return rows
