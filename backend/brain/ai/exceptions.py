"""AI Subsystem Exception Hierarchy for Auralis Brain (Phase 10.1).

Defines exception types for provider management, context/prompt building, tool routing,
and AI orchestration.
"""


class AIException(Exception):
    """Base exception for all AI subsystem errors in Auralis."""

    pass


class ProviderNotFoundError(AIException):
    """Raised when a requested AI provider is not registered in ProviderManager."""

    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        super().__init__(f"AI Provider '{provider_name}' is not registered.")


class ProviderRegistrationError(AIException):
    """Raised when registering an invalid or duplicate AI provider."""

    pass


class ProviderUnavailableError(AIException):
    """Raised when an active AI provider is unavailable or fails health check."""

    def __init__(self, provider_name: str, reason: str = ""):
        self.provider_name = provider_name
        self.reason = reason
        msg = f"AI Provider '{provider_name}' is currently unavailable."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(msg)


class ContextBuildError(AIException):
    """Raised when ContextBuilder fails to construct an AIContext."""

    pass


class PromptBuildError(AIException):
    """Raised when PromptBuilder fails to generate a Prompt."""

    pass


class ToolRoutingError(AIException):
    """Raised when ToolRouter fails to register, find, or route a tool call."""

    pass


class AIOrchestrationError(AIException):
    """Raised when AIOrchestrator pipeline execution encounters an unrecoverable failure."""

    pass
