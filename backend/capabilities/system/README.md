# System Diagnostics Capability
## Purpose
System resource monitoring and process management.

## Architecture
- `cpu.py` / `memory.py` / `storage.py` / `battery.py` / `network.py`: Profiles diagnostic resource metrics.
- `processes.py`: Monitors and terminates active OS processes.

## Relationships
- **Core:** Reports diagnostic statistics to the context builder.
- **Events:** Emits alert events if CPU/RAM thresholds are exceeded.
- **OS Layer:** Queries metrics using OSAL Process and Diagnostics Ports.
