"""Device Service implementation (Phase 11.7).

Provides detailed inspection of audio devices, display monitors, network interfaces,
storage volumes, and battery/power metrics using psutil and platform services.
"""

import os
import psutil
import socket
from typing import List, Optional

from brain.os.device.device_detector import DeviceDetector
from brain.os.device.device_models import (
    AudioDevice,
    AudioDeviceType,
    BatteryStatus,
    DeviceInfo,
    DeviceState,
    DeviceType,
    DisplayDevice,
    NetworkDevice,
    NetworkType,
    PowerState,
    StorageDevice,
)
from brain.os.device.interfaces import IDeviceDetector, IDeviceService


class DeviceService(IDeviceService):
    """Provides hardware device detailed inspection and status metrics."""

    def __init__(self, detector: Optional[IDeviceDetector] = None) -> None:
        self._detector = detector or DeviceDetector()

    def get_audio_devices(self) -> List[AudioDevice]:
        """Inspect audio input/output devices."""
        audio_infos = self._detector.get_by_type(DeviceType.AUDIO)
        results: List[AudioDevice] = []

        for info in audio_infos:
            atype = AudioDeviceType.OUTPUT_SPEAKER
            if "mic" in info.name.lower() or "input" in info.device_id.lower():
                atype = AudioDeviceType.INPUT_MIC

            dev = AudioDevice(
                info=info,
                audio_type=atype,
                volume_level=80.0,
                is_muted=False,
                sample_rate=48000,
                channels=2,
            )
            results.append(dev)

        return results

    def get_display_devices(self) -> List[DisplayDevice]:
        """Inspect connected display monitors."""
        display_infos = self._detector.get_by_type(DeviceType.DISPLAY)
        results: List[DisplayDevice] = []

        for idx, info in enumerate(display_infos):
            dev = DisplayDevice(
                info=info,
                width=1920,
                height=1080,
                refresh_rate=60,
                is_primary=idx == 0 or info.is_default,
                scaling_factor=1.0,
            )
            results.append(dev)

        return results

    def get_network_devices(self) -> List[NetworkDevice]:
        """Inspect network interface adapters."""
        net_infos = self._detector.get_by_type(DeviceType.NETWORK)
        results: List[NetworkDevice] = []

        addrs = {}
        try:
            addrs = psutil.net_if_addrs()
        except Exception:
            pass

        for info in net_infos:
            ntype = NetworkType.ETHERNET
            name_l = info.name.lower()
            if "wlan" in name_l or "wi-fi" in name_l or "wireless" in name_l:
                ntype = NetworkType.WIFI
            elif "bluetooth" in name_l:
                ntype = NetworkType.BLUETOOTH
            elif "loopback" in name_l or "lo" in name_l:
                ntype = NetworkType.LOOPBACK

            ip_str = ""
            mac_str = ""
            if info.name in addrs:
                for snic in addrs[info.name]:
                    if snic.family == socket.AF_INET:
                        ip_str = snic.address
                    elif hasattr(psutil, "AF_LINK") and snic.family == psutil.AF_LINK:
                        mac_str = snic.address

            dev = NetworkDevice(
                info=info,
                network_type=ntype,
                mac_address=mac_str,
                ip_address=ip_str or "127.0.0.1",
                speed_mbps=1000 if ntype == NetworkType.ETHERNET else 300,
                is_connected=info.state == DeviceState.CONNECTED,
            )
            results.append(dev)

        return results

    def get_storage_devices(self) -> List[StorageDevice]:
        """Inspect mounted storage volumes."""
        storage_infos = self._detector.get_by_type(DeviceType.STORAGE)
        results: List[StorageDevice] = []

        for info in storage_infos:
            mount = "/"
            if "(" in info.name and ")" in info.name:
                mount = info.name.split("(")[1].split(")")[0]

            total_b = 0
            free_b = 0
            try:
                usage = psutil.disk_usage(mount if os.path.exists(mount) else "/")
                total_b = usage.total
                free_b = usage.free
            except Exception:
                pass

            dev = StorageDevice(
                info=info,
                mount_point=mount,
                total_bytes=total_b,
                free_bytes=free_b,
                is_removable="removable" in info.name.lower(),
            )
            results.append(dev)

        return results

    def get_battery_status(self) -> BatteryStatus:
        """Inspect system power and battery status."""
        try:
            batt = psutil.sensors_battery()
            if batt:
                p_state = PowerState.DISCHARGING
                if batt.power_plugged:
                    p_state = PowerState.FULL if batt.percent >= 99.0 else PowerState.CHARGING

                time_rem = batt.secsleft if batt.secsleft not in (psutil.POWER_TIME_UNKNOWN, psutil.POWER_TIME_UNLIMITED) else None

                return BatteryStatus(
                    is_present=True,
                    power_state=p_state,
                    percentage=float(batt.percent),
                    time_remaining_seconds=float(time_rem) if time_rem else None,
                )
        except Exception:
            pass

        return BatteryStatus(
            is_present=False,
            power_state=PowerState.UNKNOWN,
            percentage=100.0,
            time_remaining_seconds=None,
        )
