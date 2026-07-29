"""Unit tests for ExecutionPolicy (Phase 9.4)."""

# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError

from brain.execution import ExecutionPolicy


def test_execution_policy_defaults() -> None:
    """Verifies default values for ExecutionPolicy."""
    policy = ExecutionPolicy()
    assert policy.maximum_retries == 3
    assert policy.maximum_timeout_seconds == 300.0
    assert policy.step_timeout_seconds == 60.0
    assert policy.continue_on_warning is True
    assert policy.continue_on_error is False
    assert policy.rollback_enabled is True
    assert policy.confirmation_required is False
    assert policy.safe_execution is True
    assert policy.metadata == {}


def test_execution_policy_custom_overrides() -> None:
    """Verifies overriding default ExecutionPolicy values."""
    policy = ExecutionPolicy(
        maximum_retries=5,
        maximum_timeout_seconds=600.0,
        step_timeout_seconds=120.0,
        continue_on_warning=False,
        continue_on_error=True,
        rollback_enabled=False,
        confirmation_required=True,
        safe_execution=False,
        metadata={"custom_flag": True},
    )
    assert policy.maximum_retries == 5
    assert policy.maximum_timeout_seconds == 600.0
    assert policy.step_timeout_seconds == 120.0
    assert policy.continue_on_warning is False
    assert policy.continue_on_error is True
    assert policy.rollback_enabled is False
    assert policy.confirmation_required is True
    assert policy.safe_execution is False
    assert policy.metadata == {"custom_flag": True}


def test_maximum_retries_validation_negative() -> None:
    """Verifies validation error when maximum_retries is negative."""
    with pytest.raises(ValidationError):
        ExecutionPolicy(maximum_retries=-1)


def test_maximum_retries_zero_allowed() -> None:
    """Verifies maximum_retries=0 is valid."""
    policy = ExecutionPolicy(maximum_retries=0)
    assert policy.maximum_retries == 0


def test_maximum_timeout_validation_zero() -> None:
    """Verifies validation error when maximum_timeout_seconds is zero or negative."""
    with pytest.raises(ValidationError):
        ExecutionPolicy(maximum_timeout_seconds=0.0)


def test_step_timeout_validation_negative() -> None:
    """Verifies validation error when step_timeout_seconds is negative."""
    with pytest.raises(ValidationError):
        ExecutionPolicy(step_timeout_seconds=-5.0)


def test_execution_policy_dict_export() -> None:
    """Verifies dictionary conversion of ExecutionPolicy."""
    policy = ExecutionPolicy(maximum_retries=2)
    data = policy.model_dump()
    assert data["maximum_retries"] == 2
    assert data["rollback_enabled"] is True


def test_execution_policy_json_export() -> None:
    """Verifies JSON string export of ExecutionPolicy."""
    policy = ExecutionPolicy(maximum_retries=2)
    json_str = policy.model_dump_json()
    assert '"maximum_retries":2' in json_str or '"maximum_retries": 2' in json_str


def test_execution_policy_copy_with_changes() -> None:
    """Verifies model_copy method on ExecutionPolicy."""
    p1 = ExecutionPolicy(maximum_retries=1)
    p2 = p1.model_copy(update={"maximum_retries": 4})
    assert p1.maximum_retries == 1
    assert p2.maximum_retries == 4


def test_execution_policy_equality() -> None:
    """Verifies equality comparison between ExecutionPolicy instances."""
    p1 = ExecutionPolicy(maximum_retries=2)
    p2 = ExecutionPolicy(maximum_retries=2)
    assert p1 == p2


def test_execution_policy_inequality() -> None:
    """Verifies inequality comparison between ExecutionPolicy instances."""
    p1 = ExecutionPolicy(maximum_retries=2)
    p2 = ExecutionPolicy(maximum_retries=4)
    assert p1 != p2


def test_execution_policy_metadata_mutation() -> None:
    """Verifies mutable metadata field behavior on policy model."""
    p = ExecutionPolicy()
    p.metadata["tag"] = "test"
    assert p.metadata["tag"] == "test"


def test_execution_policy_field_mutation() -> None:
    """Verifies mutable properties on ExecutionPolicy."""
    p = ExecutionPolicy()
    p.maximum_retries = 10
    assert p.maximum_retries == 10


def test_execution_policy_safe_execution_flag() -> None:
    """Verifies safe_execution boolean flag."""
    p = ExecutionPolicy(safe_execution=False)
    assert p.safe_execution is False


def test_execution_policy_continue_on_error_flag() -> None:
    """Verifies continue_on_error boolean flag."""
    p = ExecutionPolicy(continue_on_error=True)
    assert p.continue_on_error is True


def test_execution_policy_rollback_enabled_flag() -> None:
    """Verifies rollback_enabled boolean flag."""
    p = ExecutionPolicy(rollback_enabled=False)
    assert p.rollback_enabled is False


def test_execution_policy_confirmation_required_flag() -> None:
    """Verifies confirmation_required boolean flag."""
    p = ExecutionPolicy(confirmation_required=True)
    assert p.confirmation_required is True


def test_execution_policy_large_timeout() -> None:
    """Verifies setting large timeout values."""
    p = ExecutionPolicy(maximum_timeout_seconds=86400.0)
    assert p.maximum_timeout_seconds == 86400.0


def test_execution_policy_small_step_timeout() -> None:
    """Verifies small fractional step timeout values."""
    p = ExecutionPolicy(step_timeout_seconds=0.5)
    assert p.step_timeout_seconds == 0.5


def test_execution_policy_schema_has_all_fields() -> None:
    """Verifies all expected fields exist in JSON schema."""
    schema = ExecutionPolicy.model_json_schema()
    props = schema["properties"]
    expected_fields = [
        "maximum_retries",
        "maximum_timeout_seconds",
        "step_timeout_seconds",
        "continue_on_warning",
        "continue_on_error",
        "rollback_enabled",
        "confirmation_required",
        "safe_execution",
        "metadata",
    ]
    for field in expected_fields:
        assert field in props
