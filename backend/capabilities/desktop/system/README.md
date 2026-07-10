# System Controls Subsystem

## Purpose
Manages operating system controls through the Auralis execution pipeline, including Audio (volume & mute), Display (brightness & night light), Power (lock, sleep, hibernate, shutdown, restart), and Network (Wi-Fi & Bluetooth).

## Architecture

- **`system_service.py`**: Coordinates requests and delegates to specialized controllers.
- **`audio_controller.py`**: Manages master volume level and mute status using `pycaw`.
- **`display_controller.py`**: Manages display brightness level using WMI. Supports placeholders for Night Light.
- **`power_controller.py`**: Manages workstation lock, sleep, hibernate, restart, and shutdown states. Shutdown, restart, and hibernate require confirmation.
- **`network_controller.py`**: Manages Wi-Fi (via `netsh`) and Bluetooth (via PowerShell WinRT APIs) states.
- **`models.py`**: Declares structured `SystemStatus` Pydantic model.
