# Automation Capability
## Purpose
Orchestrates scheduled tasks and event-based macros.

## Architecture
- `scheduler.py`: Handles cron schedules.
- `triggers.py`: Evaluates event triggers.
- `conditions.py`: Checks execution state rules.
- `actions.py`: Launches automated macros.
- `workflows.py`: Coordinates sequential workflows.

## Relationships
- **Core:** Core starts automated tasks asynchronously.
- **Events:** Listens to `voice.stt_transcribed` or system boot events.
- **OS Layer:** Monitors system logs and schedules cron events.
