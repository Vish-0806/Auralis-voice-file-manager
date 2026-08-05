"""API Serialization Manager Implementation (Phase 15.5).

Thread-safe serialization manager handling in-memory model serialization, deserialization,
and dictionary conversion without networking or transport-layer overhead.
"""

from datetime import datetime, timezone
import logging
from threading import RLock
from typing import Any, Dict, Type

# pyrefly: ignore [missing-import]
from pydantic import BaseModel

from backend.application.api.validation.interfaces import (
    ISerializationManager,
)
from backend.application.api.validation.models import SerializationResult

logger = logging.getLogger(__name__)


class SerializationManager(ISerializationManager):
    """Thread-safe serialization manager converting between models, dicts, and objects."""

    def __init__(self) -> None:
        """Initialize SerializationManager using Constructor Dependency Injection."""
        self._lock = RLock()
        self._total_serializations = 0
        self._total_deserializations = 0

    def serialize(self, obj: Any) -> SerializationResult:
        """Serialize an object or Pydantic model into a dictionary data structure.

        Args:
            obj: Target object or Pydantic BaseModel instance.

        Returns:
            SerializationResult: Result snapshot of serialization operation.
        """
        with self._lock:
            self._total_serializations += 1
            try:
                if isinstance(obj, BaseModel):
                    data = obj.model_dump()
                    target_type = type(obj).__name__
                elif isinstance(obj, (dict, list, str, int, float, bool)) or obj is None:
                    data = obj
                    target_type = type(obj).__name__
                elif hasattr(obj, "__dict__"):
                    data = dict(obj.__dict__)
                    target_type = type(obj).__name__
                else:
                    data = str(obj)
                    target_type = "string"

                logger.debug("Successfully serialized object of type '%s'.", target_type)
                return SerializationResult(
                    is_success=True,
                    serialized_data=data,
                    target_type=target_type,
                    error_message=None,
                    processed_at=datetime.now(timezone.utc),
                )
            except Exception as exc:
                logger.error("Serialization error: %s", str(exc))
                return SerializationResult(
                    is_success=False,
                    serialized_data=None,
                    target_type="unknown",
                    error_message=str(exc),
                    processed_at=datetime.now(timezone.utc),
                )

    def deserialize(
        self, data: Dict[str, Any], model_class: Type[BaseModel]
    ) -> SerializationResult:
        """Deserialize a data dictionary into a target Pydantic model class.

        Args:
            data: Input dictionary.
            model_class: Target Pydantic model class subclassing BaseModel.

        Returns:
            SerializationResult: Result snapshot containing deserialized model instance.
        """
        with self._lock:
            self._total_deserializations += 1
            try:
                instance = model_class.model_validate(data)
                logger.debug("Successfully deserialized data into '%s'.", model_class.__name__)
                return SerializationResult(
                    is_success=True,
                    serialized_data=instance,
                    target_type=model_class.__name__,
                    error_message=None,
                    processed_at=datetime.now(timezone.utc),
                )
            except Exception as exc:
                logger.error("Deserialization error into '%s': %s", model_class.__name__, str(exc))
                return SerializationResult(
                    is_success=False,
                    serialized_data=None,
                    target_type=model_class.__name__,
                    error_message=str(exc),
                    processed_at=datetime.now(timezone.utc),
                )

    def to_dict(self, obj: Any) -> Dict[str, Any]:
        """Helper to convert any object or model to a plain dictionary.

        Args:
            obj: Target object.

        Returns:
            Dict[str, Any]: Plain dictionary representation.
        """
        with self._lock:
            if isinstance(obj, BaseModel):
                return obj.model_dump()
            if isinstance(obj, dict):
                return dict(obj)
            if hasattr(obj, "__dict__"):
                return dict(obj.__dict__)
            return {"value": str(obj)}

    def get_serialization_telemetry(self) -> Dict[str, int]:
        """Get internal serialization counters under lock."""
        with self._lock:
            return {
                "total_serializations": self._total_serializations,
                "total_deserializations": self._total_deserializations,
            }
