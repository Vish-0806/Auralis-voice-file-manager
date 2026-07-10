"""OS network and wireless radio controls implementation."""

from __future__ import annotations

import logging
import os
import subprocess
from typing import Any


class NetworkController:
    """Controls OS wireless radio interfaces (Wi-Fi and Bluetooth)."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initializes the NetworkController.

        Args:
            logger: Optional logger for diagnostics.
        """

        self._logger = logger or logging.getLogger(__name__)

    def enable_wifi(self) -> bool:
        """Enables the Wi-Fi network interface."""

        self._logger.info("Enabling Wi-Fi interface")
        if os.name == "nt":
            res = subprocess.run(
                ["netsh", "interface", "set", "interface", "name=Wi-Fi", "admin=enabled"],
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                return True
            self._logger.error("Failed to enable Wi-Fi via netsh", extra={"stderr": res.stderr})
            return False
        return False

    def disable_wifi(self) -> bool:
        """Disables the Wi-Fi network interface."""

        self._logger.info("Disabling Wi-Fi interface")
        if os.name == "nt":
            res = subprocess.run(
                ["netsh", "interface", "set", "interface", "name=Wi-Fi", "admin=disabled"],
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                return True
            self._logger.error("Failed to disable Wi-Fi via netsh", extra={"stderr": res.stderr})
            return False
        return False

    def enable_bluetooth(self) -> bool:
        """Enables the Bluetooth radio device using PowerShell WinRT API."""

        self._logger.info("Enabling Bluetooth radio")
        if os.name == "nt":
            script = (
                "$Assembly = [System.Reflection.Assembly]::LoadWithPartialName('System.Runtime.WindowsRuntime'); "
                "$RadioType = [Windows.Devices.Radios.Radio, Windows.Devices.Sensors, ContentType=WindowsRuntime]; "
                "$RadiosTask = [Windows.Devices.Radios.Radio]::GetRadiosAsync(); "
                "while (-not $RadiosTask.IsCompleted) { Start-Sleep -Milliseconds 10 }; "
                "$Bluetooth = $RadiosTask.GetResults() | Where-Object { $_.Kind -eq 'Bluetooth' }; "
                "if ($Bluetooth) { "
                "  $StateTask = $Bluetooth.SetStateAsync('On'); "
                "  while (-not $StateTask.IsCompleted) { Start-Sleep -Milliseconds 10 }; "
                "  exit 0; "
                "} "
                "exit 1;"
            )
            res = subprocess.run(
                ["powershell", "-Command", script],
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                return True
            self._logger.error("Failed to enable Bluetooth via WinRT PowerShell", extra={"stderr": res.stderr})
            return False
        return False

    def disable_bluetooth(self) -> bool:
        """Disables the Bluetooth radio device using PowerShell WinRT API."""

        self._logger.info("Disabling Bluetooth radio")
        if os.name == "nt":
            script = (
                "$Assembly = [System.Reflection.Assembly]::LoadWithPartialName('System.Runtime.WindowsRuntime'); "
                "$RadioType = [Windows.Devices.Radios.Radio, Windows.Devices.Sensors, ContentType=WindowsRuntime]; "
                "$RadiosTask = [Windows.Devices.Radios.Radio]::GetRadiosAsync(); "
                "while (-not $RadiosTask.IsCompleted) { Start-Sleep -Milliseconds 10 }; "
                "$Bluetooth = $RadiosTask.GetResults() | Where-Object { $_.Kind -eq 'Bluetooth' }; "
                "if ($Bluetooth) { "
                "  $StateTask = $Bluetooth.SetStateAsync('Off'); "
                "  while (-not $StateTask.IsCompleted) { Start-Sleep -Milliseconds 10 }; "
                "  exit 0; "
                "} "
                "exit 1;"
            )
            res = subprocess.run(
                ["powershell", "-Command", script],
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                return True
            self._logger.error("Failed to disable Bluetooth via WinRT PowerShell", extra={"stderr": res.stderr})
            return False
        return False

    def network_status(self) -> dict[str, Any]:
        """Queries the status of wireless network interfaces.

        Returns:
            A dictionary containing status values.
        """

        wifi_ok = False
        bt_ok = False

        if os.name == "nt":
            try:
                res = subprocess.run(
                    ["netsh", "interface", "show", "interface", "name=Wi-Fi"],
                    capture_output=True,
                    text=True,
                )
                if "Enabled" in res.stdout and "Connected" in res.stdout:
                    wifi_ok = True
                elif "Enabled" in res.stdout:
                    wifi_ok = True
            except Exception:
                pass

            try:
                script = (
                    "$Assembly = [System.Reflection.Assembly]::LoadWithPartialName('System.Runtime.WindowsRuntime'); "
                    "$RadioType = [Windows.Devices.Radios.Radio, Windows.Devices.Sensors, ContentType=WindowsRuntime]; "
                    "$RadiosTask = [Windows.Devices.Radios.Radio]::GetRadiosAsync(); "
                    "while (-not $RadiosTask.IsCompleted) { Start-Sleep -Milliseconds 10 }; "
                    "$Bluetooth = $RadiosTask.GetResults() | Where-Object { $_.Kind -eq 'Bluetooth' }; "
                    "if ($Bluetooth -and $Bluetooth.State -eq 'On') { exit 0 } else { exit 1 }"
                )
                res = subprocess.run(
                    ["powershell", "-Command", script],
                    capture_output=True,
                )
                if res.returncode == 0:
                    bt_ok = True
            except Exception:
                pass

        return {
            "wifi_enabled": wifi_ok,
            "bluetooth_enabled": bt_ok,
        }
