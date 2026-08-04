"""Configuration Runtime Singleton Accessors (Phase 14.3.1).

Thread-safe lazy singleton accessors for IConfigurationRuntime and IConfigurationProvider.
"""

import logging
from threading import RLock
from typing import Optional

from backend.application.config.configuration_provider import ConfigurationProvider
from backend.application.config.configuration_runtime import ConfigurationRuntime
from backend.application.config.interfaces import IConfigurationProvider, IConfigurationRuntime

logger = logging.getLogger(__name__)

_RUNTIME_LOCK = RLock()
_GLOBAL_CONFIGURATION_RUNTIME: Optional[IConfigurationRuntime] = None
_GLOBAL_CONFIGURATION_PROVIDER: Optional[IConfigurationProvider] = None


def get_configuration_runtime() -> IConfigurationRuntime:
    """Get global IConfigurationRuntime singleton instance (lazy initialization).

    Returns:
        IConfigurationRuntime: Global runtime instance.
    """
    global _GLOBAL_CONFIGURATION_RUNTIME
    with _RUNTIME_LOCK:
        if _GLOBAL_CONFIGURATION_RUNTIME is None:
            provider = get_configuration_provider()
            _GLOBAL_CONFIGURATION_RUNTIME = ConfigurationRuntime(provider=provider)
            logger.info("Initialized global IConfigurationRuntime singleton.")
        return _GLOBAL_CONFIGURATION_RUNTIME


def set_configuration_runtime(runtime: IConfigurationRuntime) -> None:
    """Set custom global IConfigurationRuntime singleton instance.

    Args:
        runtime: Target IConfigurationRuntime implementation instance.
    """
    global _GLOBAL_CONFIGURATION_RUNTIME
    with _RUNTIME_LOCK:
        _GLOBAL_CONFIGURATION_RUNTIME = runtime
        logger.info("Updated global IConfigurationRuntime singleton.")


def reset_configuration_runtime() -> None:
    """Reset global IConfigurationRuntime singleton instance to None."""
    global _GLOBAL_CONFIGURATION_RUNTIME
    with _RUNTIME_LOCK:
        if _GLOBAL_CONFIGURATION_RUNTIME is not None:
            try:
                _GLOBAL_CONFIGURATION_RUNTIME.shutdown()
            except Exception as exc:
                logger.warning("Error during global ConfigurationRuntime reset shutdown: %s", exc)
            _GLOBAL_CONFIGURATION_RUNTIME = None
            logger.info("Reset global IConfigurationRuntime singleton.")


def get_configuration_provider() -> IConfigurationProvider:
    """Get global IConfigurationProvider singleton instance (lazy initialization).

    Returns:
        IConfigurationProvider: Global provider instance.
    """
    global _GLOBAL_CONFIGURATION_PROVIDER
    with _RUNTIME_LOCK:
        if _GLOBAL_CONFIGURATION_PROVIDER is None:
            _GLOBAL_CONFIGURATION_PROVIDER = ConfigurationProvider()
            logger.info("Initialized global IConfigurationProvider singleton.")
        return _GLOBAL_CONFIGURATION_PROVIDER


def set_configuration_provider(provider: IConfigurationProvider) -> None:
    """Set custom global IConfigurationProvider singleton instance.

    Args:
        provider: Target IConfigurationProvider implementation instance.
    """
    global _GLOBAL_CONFIGURATION_PROVIDER
    with _RUNTIME_LOCK:
        _GLOBAL_CONFIGURATION_PROVIDER = provider
        logger.info("Updated global IConfigurationProvider singleton.")


def reset_configuration_provider() -> None:
    """Reset global IConfigurationProvider singleton instance to None."""
    global _GLOBAL_CONFIGURATION_PROVIDER
    with _RUNTIME_LOCK:
        if _GLOBAL_CONFIGURATION_PROVIDER is not None:
            try:
                _GLOBAL_CONFIGURATION_PROVIDER.shutdown()
            except Exception as exc:
                logger.warning("Error during global ConfigurationProvider reset shutdown: %s", exc)
            _GLOBAL_CONFIGURATION_PROVIDER = None
            logger.info("Reset global IConfigurationProvider singleton.")
