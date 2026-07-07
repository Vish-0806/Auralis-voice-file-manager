"""Voice pipeline integration package.

Exposes EventRouter, VoicePipeline, and PipelineController to stitch all voice blocks
into an end-to-end OS Assistant execution flow.
"""

from voice.integration.event_router import EventRouter
from voice.integration.voice_pipeline import VoicePipeline
from voice.integration.pipeline_controller import PipelineController

__all__ = [
    "EventRouter",
    "VoicePipeline",
    "PipelineController",
]
