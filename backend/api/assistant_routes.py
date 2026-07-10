"""Assistant REST API routes for Auralis.

This module exposes the assistant orchestration pipeline through standard
HTTP endpoints. It keeps the API layer thin by delegating request execution to
the core assistant, planner, and dispatcher collaborators.
"""

from __future__ import annotations

import logging
import platform
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from capabilities.desktop import DesktopCapability
from capabilities.files import FileCapability
from core.assistant import AuralisAssistant, get_assistant, set_assistant_instance
from core.dispatcher import ActionDispatcher
from core.models import AssistantRequest, AssistantResponse
from core.planner import Planner
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["assistant"])


class HealthResponse(BaseModel):
    """Represents the service health payload."""

    status: str = Field(default="ok")
    version: str
    timestamp: datetime


class PlatformInfo(BaseModel):
    """Represents host platform information exposed by the status endpoint."""

    system: str
    release: str
    version: str
    machine: str
    python_version: str


class StatusResponse(BaseModel):
    """Represents the service status payload."""

    platform: PlatformInfo
    loaded_capabilities: list[str]
    assistant_status: str


def get_assistant_dependency() -> AuralisAssistant:
    """Returns a configured assistant instance for route handlers.

    The repository currently relies on a singleton assistant in the core
    layer. This dependency ensures the singleton is available even when the
    application has not explicitly registered one yet.

    Returns:
        The configured assistant instance.
    """

    try:
        return get_assistant()
    except RuntimeError:
        assistant = _build_default_assistant()
        set_assistant_instance(assistant)
        logger.info("Initialized default assistant instance for REST API")
        return assistant


def _build_default_assistant() -> AuralisAssistant:
    """Builds the default assistant stack used by the API dependency."""

    planner = Planner()
    file_capability = FileCapability()
    desktop_capability = DesktopCapability()
    dispatcher = ActionDispatcher(capabilities={
        file_capability.name: file_capability,
        desktop_capability.name: desktop_capability,
    })
    return AuralisAssistant(planner=planner, dispatcher=dispatcher)


def _get_loaded_capabilities(assistant: AuralisAssistant) -> list[str]:
    """Extracts loaded capability names from the assistant dispatcher."""

    dispatcher = getattr(assistant, "_dispatcher", None)
    capability_names: list[str] = []

    if dispatcher is not None:
        capabilities = getattr(dispatcher, "_capabilities", {})
        if isinstance(capabilities, dict):
            capability_names = sorted(str(name) for name in capabilities.keys())

    return capability_names


@router.get("/health", response_model=HealthResponse)
def get_health(request: Request) -> HealthResponse:
    """Returns a lightweight health payload for the service."""

    version = request.app.version or "unknown"
    return HealthResponse(
        status="ok",
        version=version,
        timestamp=datetime.now(UTC),
    )


@router.get("/status", response_model=StatusResponse)
def get_status(assistant: AuralisAssistant = Depends(get_assistant_dependency)) -> StatusResponse:
    """Returns service and assistant status information."""

    platform_info = PlatformInfo(
        system=platform.system(),
        release=platform.release(),
        version=platform.version(),
        machine=platform.machine(),
        python_version=platform.python_version(),
    )
    return StatusResponse(
        platform=platform_info,
        loaded_capabilities=_get_loaded_capabilities(assistant),
        assistant_status="ready",
    )


@router.post("/assistant", response_model=AssistantResponse)
def post_assistant(
    request: AssistantRequest,
    assistant: AuralisAssistant = Depends(get_assistant_dependency),
) -> AssistantResponse:
    """Processes an assistant request through the core execution pipeline."""

    try:
        logger.info("Received assistant request", extra={"source": request.source})
        return assistant.process_request(request)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Assistant request failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process assistant request: {exc}",
        ) from exc


__all__ = [
    "router",
    "get_assistant_dependency",
    "HealthResponse",
    "StatusResponse",
    "PlatformInfo",
]