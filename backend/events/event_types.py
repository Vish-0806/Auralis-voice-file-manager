"""
Module: backend.events.event_types

Responsibility:
    Declares the standard event type strings and category enums.
    Enforces unified naming conventions across all event publishers and subscribers.

This module SHOULD:
    - Define an EventCategory enum representing functional sub-systems.
    - Declare a class containing constants or string names for all supported system events.
    - Structure events with namespace dot notation (e.g., "voice.wake_word_detected").

This module should NEVER:
    - Include logic for routing or dispatching events.
    - Interface with external configurations or databases.
    - Include executable classes.
"""

import enum


class EventCategory(enum.Enum):
    """Broad categories of functional sub-systems in Auralis."""
    SYSTEM = "system"
    VOICE = "voice"
    AI = "ai"
    CAPABILITY = "capability"
    STORAGE = "storage"
    AUTOMATION = "automation"


class SystemEvents:
    """Namespace definitions for standard system events."""
    
    # System Lifecycle
    SYSTEM_BOOT = "system.boot"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"

    # Voice Engine
    WAKE_WORD_DETECTED = "voice.wake_word_detected"
    SPEECH_STARTED = "voice.speech_started"
    SPEECH_COMPLETED = "voice.speech_completed"
    STT_TRANSCRIBED = "voice.stt_transcribed"
    TTS_PLAYBACK_STARTED = "voice.tts_playback_started"

    # AI Brain
    PLANNING_STARTED = "ai.planning_started"
    PLANNING_COMPLETED = "ai.planning_completed"
    TOOL_CALL_REQUESTED = "ai.tool_call_requested"
    SAFETY_AUDIT_COMPLETED = "ai.safety_audit_completed"

    # Capabilities
    FILE_CREATED = "capability.file_created"
    FILE_DELETED = "capability.file_deleted"
    TASK_RUNNER_STARTED = "capability.task_runner_started"
    PROCESS_TERMINATED = "capability.process_terminated"

    # Automation
    AUTOMATION_TRIGGERED = "automation.triggered"
    AUTOMATION_COMPLETED = "automation.completed"
    CRON_FIRED = "automation.cron_fired"

    # Storage
    SQLITE_UPDATED = "storage.sqlite_updated"
    VECTOR_INDEX_REBUILT = "storage.vector_index_rebuilt"
