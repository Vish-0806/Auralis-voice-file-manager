"""Tests for API Validation & Serialization Runtime (Phase 15.5).

Validates immutable models, enums, exception hierarchy, ABC interfaces,
schema registry, validation engine, serialization manager, provider lifecycle,
runtime coordinator, lazy singletons, and multithreaded concurrency.
"""

from concurrent.futures import ThreadPoolExecutor
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, ValidationError as PydanticValidationError

from backend.application.api.validation import (
    DeserializationException,
    ISchemaRegistry,
    ISerializationManager,
    IValidationEngine,
    IValidationProvider,
    IValidationRuntime,
    SchemaRegistrationException,
    SchemaRegistry,
    SerializationException,
    SerializationManager,
    SerializationResult,
    ValidationCapabilities,
    ValidationContext,
    ValidationDiagnostics,
    ValidationError,
    ValidationEngine,
    ValidationException,
    ValidationFailureException,
    ValidationField,
    ValidationHealth,
    ValidationProvider,
    ValidationResult,
    ValidationRule,
    ValidationRuntime,
    ValidationRuntimeState,
    ValidationSchema,
    ValidationSeverity,
    ValidationState,
    ValidationStatistics,
    get_validation_provider,
    get_validation_runtime,
    reset_validation_provider,
    reset_validation_runtime,
    set_validation_provider,
    set_validation_runtime,
)


class DummySampleModel(BaseModel):
    """Sample model for serialization tests."""

    name: str
    age: int


@pytest.fixture(autouse=True)
def _reset_validation_singletons():
    """Reset validation singletons before and after each test."""
    reset_validation_runtime()
    reset_validation_provider()
    yield
    reset_validation_runtime()
    reset_validation_provider()


# --- Enum Tests ---

def test_enum_validation_severity():
    """Verify ValidationSeverity enum values."""
    assert ValidationSeverity.INFO.value == "INFO"
    assert ValidationSeverity.WARNING.value == "WARNING"
    assert ValidationSeverity.ERROR.value == "ERROR"
    assert len(ValidationSeverity) == 3


def test_enum_validation_state():
    """Verify ValidationState enum values."""
    assert ValidationState.VALID.value == "VALID"
    assert ValidationState.INVALID.value == "INVALID"
    assert ValidationState.SKIPPED.value == "SKIPPED"
    assert len(ValidationState) == 3


def test_enum_validation_runtime_state():
    """Verify ValidationRuntimeState enum values."""
    assert ValidationRuntimeState.UNINITIALIZED.value == "UNINITIALIZED"
    assert ValidationRuntimeState.INITIALIZING.value == "INITIALIZING"
    assert ValidationRuntimeState.READY.value == "READY"
    assert ValidationRuntimeState.STOPPING.value == "STOPPING"
    assert ValidationRuntimeState.STOPPED.value == "STOPPED"
    assert len(ValidationRuntimeState) == 5


# --- Model Immutability Tests ---

def test_model_immutability_validation_rule():
    """Verify ValidationRule defaults and immutability."""
    rule = ValidationRule(rule_id="r1", name="MinLength", rule_type="min_length")
    assert rule.rule_id == "r1"
    assert rule.rule_type == "min_length"

    with pytest.raises((PydanticValidationError, TypeError)):
        rule.name = "NewName"  # type: ignore[attr-defined]


def test_model_immutability_validation_field():
    """Verify ValidationField defaults and immutability."""
    field = ValidationField(field_name="email", field_type="str", required=True)
    assert field.field_name == "email"
    assert field.required is True

    with pytest.raises((PydanticValidationError, TypeError)):
        field.required = False  # type: ignore[attr-defined]


def test_model_immutability_validation_schema():
    """Verify ValidationSchema defaults and immutability."""
    schema = ValidationSchema(schema_id="s1", name="UserSchema")
    assert schema.schema_id == "s1"
    assert schema.version == "1.0.0"

    with pytest.raises((PydanticValidationError, TypeError)):
        schema.name = "NewSchema"  # type: ignore[attr-defined]


def test_model_immutability_validation_error():
    """Verify ValidationError defaults and immutability."""
    err = ValidationError(error_id="e1", field_name="age", message="Too young")
    assert err.error_id == "e1"
    assert err.severity == ValidationSeverity.ERROR

    with pytest.raises((PydanticValidationError, TypeError)):
        err.message = "Different"  # type: ignore[attr-defined]


def test_model_immutability_validation_result():
    """Verify ValidationResult defaults and immutability."""
    res = ValidationResult(is_valid=True)
    assert res.is_valid is True
    assert res.state == ValidationState.VALID

    with pytest.raises((PydanticValidationError, TypeError)):
        res.is_valid = False  # type: ignore[attr-defined]


def test_model_immutability_serialization_result():
    """Verify SerializationResult defaults and immutability."""
    res = SerializationResult(is_success=True, serialized_data={"a": 1})
    assert res.is_success is True

    with pytest.raises((PydanticValidationError, TypeError)):
        res.is_success = False  # type: ignore[attr-defined]


def test_model_immutability_validation_context():
    """Verify ValidationContext defaults and immutability."""
    ctx = ValidationContext(context_id="c1", schema_id="s1")
    assert ctx.context_id == "c1"

    with pytest.raises((PydanticValidationError, TypeError)):
        ctx.context_id = "c2"  # type: ignore[attr-defined]


def test_model_immutability_capabilities():
    """Verify ValidationCapabilities defaults and immutability."""
    caps = ValidationCapabilities()
    assert caps.supports_schema_registration is True

    with pytest.raises((PydanticValidationError, TypeError)):
        caps.supports_schema_registration = False  # type: ignore[attr-defined]


def test_model_immutability_statistics():
    """Verify ValidationStatistics defaults and immutability."""
    stats = ValidationStatistics()
    assert stats.total_schemas == 0

    with pytest.raises((PydanticValidationError, TypeError)):
        stats.total_schemas = 5  # type: ignore[attr-defined]


def test_model_immutability_health():
    """Verify ValidationHealth defaults and immutability."""
    health = ValidationHealth()
    assert health.is_healthy is True

    with pytest.raises((PydanticValidationError, TypeError)):
        health.is_healthy = False  # type: ignore[attr-defined]


def test_model_immutability_diagnostics():
    """Verify ValidationDiagnostics defaults and immutability."""
    diag = ValidationDiagnostics()
    assert diag.registered_schemas_count == 0

    with pytest.raises((PydanticValidationError, TypeError)):
        diag.registered_schemas_count = 10  # type: ignore[attr-defined]


# --- Exception Hierarchy Tests ---

def test_exception_hierarchy():
    """Verify exception hierarchy inheritance."""
    assert issubclass(SchemaRegistrationException, ValidationException)
    assert issubclass(ValidationFailureException, ValidationException)
    assert issubclass(SerializationException, ValidationException)
    assert issubclass(DeserializationException, ValidationException)
    assert issubclass(ValidationException, Exception)


# --- Interface Abstraction Tests ---

def test_interfaces_cannot_be_instantiated():
    """Verify abstract base classes raise TypeError on direct instantiation."""
    with pytest.raises(TypeError):
        ISchemaRegistry()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IValidationEngine()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        ISerializationManager()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IValidationProvider()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IValidationRuntime()  # type: ignore[abstract]


# --- SchemaRegistry Tests ---

def test_registry_register_and_lookup():
    """Verify registering and looking up a ValidationSchema."""
    registry = SchemaRegistry()
    schema = ValidationSchema(schema_id="s1", name="TestSchema")
    registered = registry.register_schema(schema)

    assert registered.schema_id == "s1"
    assert registry.lookup_schema("s1") == schema
    assert registry.count_schemas() == 1


def test_registry_duplicate_schema_exception():
    """Verify SchemaRegistrationException on duplicate schema ID."""
    registry = SchemaRegistry()
    schema1 = ValidationSchema(schema_id="s1", name="Schema1")
    schema2 = ValidationSchema(schema_id="s1", name="Schema2")

    registry.register_schema(schema1)
    with pytest.raises(SchemaRegistrationException):
        registry.register_schema(schema2)


def test_registry_unregister():
    """Verify unregistering a schema."""
    registry = SchemaRegistry()
    schema = ValidationSchema(schema_id="s1", name="TestSchema")
    registry.register_schema(schema)

    removed = registry.unregister_schema("s1")
    assert removed == schema
    assert registry.lookup_schema("s1") is None
    assert registry.count_schemas() == 0


def test_registry_list_and_count():
    """Verify list_schemas and count_schemas."""
    registry = SchemaRegistry()
    registry.register_schema(ValidationSchema(schema_id="s1", name="S1"))
    registry.register_schema(ValidationSchema(schema_id="s2", name="S2"))

    assert registry.count_schemas() == 2
    assert len(registry.list_schemas()) == 2


def test_registry_clear():
    """Verify clearing all schemas from registry."""
    registry = SchemaRegistry()
    registry.register_schema(ValidationSchema(schema_id="s1", name="S1"))
    registry.register_schema(ValidationSchema(schema_id="s2", name="S2"))

    registry.clear()
    assert registry.count_schemas() == 0


# --- ValidationEngine Tests ---

def test_engine_validate_success():
    """Verify successful validation when data matches schema."""
    field1 = ValidationField(field_name="username", field_type="str", required=True)
    field2 = ValidationField(field_name="age", field_type="int", required=True)
    schema = ValidationSchema(schema_id="s1", name="User", fields=(field1, field2))

    registry = SchemaRegistry()
    registry.register_schema(schema)

    engine = ValidationEngine(registry=registry)
    result = engine.validate("s1", {"username": "alice", "age": 30})

    assert result.is_valid is True
    assert result.state == ValidationState.VALID
    assert len(result.errors) == 0


def test_engine_validate_missing_required_field():
    """Verify validation failure when required field is missing."""
    field1 = ValidationField(field_name="username", field_type="str", required=True)
    schema = ValidationSchema(schema_id="s1", name="User", fields=(field1,))

    registry = SchemaRegistry()
    registry.register_schema(schema)

    engine = ValidationEngine(registry=registry)
    result = engine.validate("s1", {})

    assert result.is_valid is False
    assert result.state == ValidationState.INVALID
    assert len(result.errors) == 1
    assert result.errors[0].field_name == "username"
    assert result.errors[0].rule_name == "required"


def test_engine_validate_type_mismatch():
    """Verify validation failure on type mismatch."""
    field1 = ValidationField(field_name="age", field_type="int", required=True)
    schema = ValidationSchema(schema_id="s1", name="User", fields=(field1,))

    registry = SchemaRegistry()
    registry.register_schema(schema)

    engine = ValidationEngine(registry=registry)
    result = engine.validate("s1", {"age": "thirty"})

    assert result.is_valid is False
    assert len(result.errors) == 1
    assert result.errors[0].rule_name == "type_check"


def test_engine_validate_min_length_rule():
    """Verify min_length rule enforcement."""
    rule = ValidationRule(rule_id="r1", name="min_len", rule_type="min_length", params={"min_length": 5})
    field = ValidationField(field_name="bio", field_type="str", required=True, rules=(rule,))
    schema = ValidationSchema(schema_id="s1", name="Profile", fields=(field,))

    engine = ValidationEngine()
    result = engine.validate_with_schema(schema, {"bio": "hi"})

    assert result.is_valid is False
    assert len(result.errors) == 1
    assert result.errors[0].rule_name == "min_len"


def test_engine_validate_max_length_rule():
    """Verify max_length rule enforcement."""
    rule = ValidationRule(rule_id="r1", name="max_len", rule_type="max_length", params={"max_length": 5})
    field = ValidationField(field_name="tag", field_type="str", required=True, rules=(rule,))
    schema = ValidationSchema(schema_id="s1", name="Tag", fields=(field,))

    engine = ValidationEngine()
    result = engine.validate_with_schema(schema, {"tag": "long_tag_name"})

    assert result.is_valid is False
    assert len(result.errors) == 1


def test_engine_validate_min_rule():
    """Verify min rule enforcement on numeric values."""
    rule = ValidationRule(rule_id="r1", name="min_age", rule_type="min", params={"min": 18})
    field = ValidationField(field_name="age", field_type="int", required=True, rules=(rule,))
    schema = ValidationSchema(schema_id="s1", name="Adult", fields=(field,))

    engine = ValidationEngine()
    result = engine.validate_with_schema(schema, {"age": 16})

    assert result.is_valid is False
    assert len(result.errors) == 1


def test_engine_validate_max_rule():
    """Verify max rule enforcement on numeric values."""
    rule = ValidationRule(rule_id="r1", name="max_score", rule_type="max", params={"max": 100})
    field = ValidationField(field_name="score", field_type="int", required=True, rules=(rule,))
    schema = ValidationSchema(schema_id="s1", name="Exam", fields=(field,))

    engine = ValidationEngine()
    result = engine.validate_with_schema(schema, {"score": 105})

    assert result.is_valid is False
    assert len(result.errors) == 1


def test_engine_validate_unregistered_schema():
    """Verify error result when schema is not found."""
    engine = ValidationEngine()
    result = engine.validate("missing_schema", {"a": 1})

    assert result.is_valid is False
    assert len(result.errors) == 1
    assert result.errors[0].rule_name == "schema_exists"


def test_engine_boolean_type_check_edge_case():
    """Verify boolean is not falsely matched as integer."""
    field = ValidationField(field_name="count", field_type="int", required=True)
    schema = ValidationSchema(schema_id="s1", name="Count", fields=(field,))

    engine = ValidationEngine()
    result = engine.validate_with_schema(schema, {"count": True})

    assert result.is_valid is False


def test_schema_optional_fields_pass_validation():
    """Verify optional fields pass when omitted."""
    field = ValidationField(field_name="nickname", field_type="str", required=False)
    schema = ValidationSchema(schema_id="s1", name="Opt", fields=(field,))

    engine = ValidationEngine()
    result = engine.validate_with_schema(schema, {})

    assert result.is_valid is True


def test_engine_validate_direct_with_schema():
    """Verify validate_with_schema directly."""
    field = ValidationField(field_name="city", field_type="str", required=True)
    schema = ValidationSchema(schema_id="s1", name="City", fields=(field,))

    engine = ValidationEngine()
    result = engine.validate_with_schema(schema, {"city": "Seattle"})
    assert result.is_valid is True


# --- SerializationManager Tests ---

def test_serialization_manager_serialize_model():
    """Verify serializing a Pydantic BaseModel instance."""
    mgr = SerializationManager()
    model = DummySampleModel(name="alice", age=30)
    result = mgr.serialize(model)

    assert result.is_success is True
    assert result.serialized_data == {"name": "alice", "age": 30}
    assert result.target_type == "DummySampleModel"


def test_serialization_manager_serialize_dict():
    """Verify serializing a standard dictionary."""
    mgr = SerializationManager()
    data = {"key": "value"}
    result = mgr.serialize(data)

    assert result.is_success is True
    assert result.serialized_data == data


def test_serialization_manager_deserialize_valid_model():
    """Verify deserializing a valid dict into a Pydantic model class."""
    mgr = SerializationManager()
    data = {"name": "bob", "age": 25}
    result = mgr.deserialize(data, DummySampleModel)

    assert result.is_success is True
    assert isinstance(result.serialized_data, DummySampleModel)
    assert result.serialized_data.name == "bob"


def test_serialization_manager_deserialize_invalid_model():
    """Verify deserialization error handling on invalid data."""
    mgr = SerializationManager()
    data = {"name": "bob"}  # missing 'age'
    result = mgr.deserialize(data, DummySampleModel)

    assert result.is_success is False
    assert result.error_message is not None


def test_serialization_manager_to_dict_helper():
    """Verify to_dict helper conversion."""
    mgr = SerializationManager()
    model = DummySampleModel(name="alice", age=30)

    d1 = mgr.to_dict(model)
    assert d1 == {"name": "alice", "age": 30}

    d2 = mgr.to_dict({"x": 1})
    assert d2 == {"x": 1}


# --- ValidationProvider Tests ---

def test_provider_lifecycle():
    """Verify ValidationProvider initialize and shutdown transitions."""
    provider = ValidationProvider()
    assert provider.health().state == ValidationRuntimeState.UNINITIALIZED

    health1 = provider.initialize()
    assert health1.state == ValidationRuntimeState.READY
    assert health1.is_healthy is True

    health2 = provider.shutdown()
    assert health2.state == ValidationRuntimeState.STOPPED
    assert health2.is_healthy is False


def test_provider_restart():
    """Verify ValidationProvider restart cycle."""
    provider = ValidationProvider()
    provider.initialize()

    health = provider.restart()
    assert health.state == ValidationRuntimeState.READY
    assert provider.statistics().metrics.get("total_restarts") == 1.0


def test_provider_health_stats_caps_diag():
    """Verify health, statistics, capabilities, and diagnostics from provider."""
    registry = SchemaRegistry()
    registry.register_schema(ValidationSchema(schema_id="s1", name="S1"))

    provider = ValidationProvider(schema_registry=registry)
    provider.initialize()

    assert provider.health().is_healthy is True
    assert provider.statistics().total_schemas == 1
    assert provider.capabilities().supports_field_validation is True
    assert provider.diagnostics().registered_schemas_count == 1


# --- ValidationRuntime Tests ---

def test_runtime_lifecycle_delegation():
    """Verify ValidationRuntime delegates lifecycle calls to provider."""
    runtime = ValidationRuntime()
    assert runtime.health().state == ValidationRuntimeState.UNINITIALIZED

    runtime.initialize()
    assert runtime.health().state == ValidationRuntimeState.READY

    runtime.shutdown()
    assert runtime.health().state == ValidationRuntimeState.STOPPED


def test_constructor_dependency_injection():
    """Verify Constructor DI in ValidationProvider and ValidationRuntime."""
    registry = SchemaRegistry()
    engine = ValidationEngine(registry=registry)
    ser_mgr = SerializationManager()

    provider = ValidationProvider(
        schema_registry=registry,
        validation_engine=engine,
        serialization_manager=ser_mgr,
    )
    runtime = ValidationRuntime(provider=provider)

    assert runtime.get_provider().get_schema_registry() is registry
    assert runtime.get_provider().get_validation_engine() is engine
    assert runtime.get_provider().get_serialization_manager() is ser_mgr


# --- Lazy Singleton Helper Tests ---

def test_lazy_singleton_validation_runtime():
    """Verify get_validation_runtime, set_validation_runtime, and reset_validation_runtime."""
    r1 = get_validation_runtime()
    r2 = get_validation_runtime()
    assert r1 is r2
    assert isinstance(r1, ValidationRuntime)

    custom = ValidationRuntime()
    set_validation_runtime(custom)
    assert get_validation_runtime() is custom

    reset_validation_runtime()
    r3 = get_validation_runtime()
    assert r3 is not custom


def test_lazy_singleton_validation_provider():
    """Verify get_validation_provider, set_validation_provider, and reset_validation_provider."""
    p1 = get_validation_provider()
    p2 = get_validation_provider()
    assert p1 is p2
    assert isinstance(p1, ValidationProvider)

    custom = ValidationProvider()
    set_validation_provider(custom)
    assert get_validation_provider() is custom

    reset_validation_provider()
    p3 = get_validation_provider()
    assert p3 is not custom


# --- Concurrency Tests ---

def test_concurrent_registry_operations():
    """Verify thread-safety of SchemaRegistry under concurrent schema registrations."""
    registry = SchemaRegistry()

    def register_worker(idx: int):
        registry.register_schema(ValidationSchema(schema_id=f"s_{idx}", name=f"Schema_{idx}"))

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(register_worker, i) for i in range(40)]
        for f in futures:
            f.result()

    assert registry.count_schemas() == 40


def test_concurrent_engine_validations():
    """Verify thread-safety of ValidationEngine under concurrent validations."""
    field = ValidationField(field_name="val", field_type="int", required=True)
    schema = ValidationSchema(schema_id="s_shared", name="Shared", fields=(field,))

    registry = SchemaRegistry()
    registry.register_schema(schema)
    engine = ValidationEngine(registry=registry)

    def validate_worker(idx: int):
        return engine.validate("s_shared", {"val": idx})

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(validate_worker, i) for i in range(50)]
        results = [f.result() for f in futures]

    assert len(results) == 50
    assert all(r.is_valid for r in results)


def test_concurrent_serialization_operations():
    """Verify thread-safety of SerializationManager under concurrent operations."""
    mgr = SerializationManager()

    def serialize_worker(idx: int):
        model = DummySampleModel(name=f"user_{idx}", age=idx)
        res1 = mgr.serialize(model)
        res2 = mgr.deserialize({"name": f"user_{idx}", "age": idx}, DummySampleModel)
        return res1.is_success and res2.is_success

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(serialize_worker, i) for i in range(50)]
        results = [f.result() for f in futures]

    assert len(results) == 50
    assert all(results)
