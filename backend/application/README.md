# Application Container & Infrastructure Platform (Phase 14)

The `backend/application/` package provides the core **Application Container & Infrastructure Platform** for Auralis. It establishes enterprise-grade application lifecycle management, thread-safe dependency injection, and certified multi-source configuration management.

---

## 1. Directory Structure

```
backend/application/
├── config/                         # Certified Configuration Runtime Subsystem (Phase 14.3)
│   ├── configuration_certifier.py  # Production Certification Engine (Phase 14.3.6)
│   ├── configuration_provider.py   # Runtime Coordination Provider (Phase 14.3.1)
│   ├── configuration_resolver.py   # Type Conversion & Resolution Engine (Phase 14.3.3)
│   ├── configuration_runtime.py    # Runtime Lifecycle Manager (Phase 14.3.1)
│   ├── configuration_schema.py     # Schema Property Definition Manager (Phase 14.3.3)
│   ├── configuration_source_manager.py # Priority Source Manager (Phase 14.3.2)
│   ├── configuration_validator.py  # Property Constraint Validator (Phase 14.3.3)
│   ├── dotenv_source.py            # DotEnv File Source (Phase 14.3.2)
│   ├── environment_source.py       # OS Environment Source (Phase 14.3.2)
│   ├── exceptions.py               # Exception Hierarchy (Phase 14.3.1)
│   ├── feature_flag_manager.py     # Feature Flags & Rollout Engine (Phase 14.3.4)
│   ├── interfaces.py               # Configuration ABC Interfaces (Phase 14.3.1)
│   ├── memory_source.py            # In-Memory Source (Phase 14.3.2)
│   ├── models.py                   # Immutable Pydantic v2 Models (Phase 14.3.1)
│   ├── profile_manager.py          # Profiles & Overrides Manager (Phase 14.3.4)
│   ├── runtime.py                  # Lazy Singleton Accessors (Phase 14.3.1)
│   ├── secret_manager.py           # Secret Redaction & Policy Manager (Phase 14.3.5)
│   ├── secret_store.py             # In-Memory Secure Secret Store (Phase 14.3.5)
│   └── source_registry.py          # Source Registration & Priority Registry (Phase 14.3.2)
├── di/                             # Dependency Injection Subsystem (Phase 14.2)
│   ├── container_scope.py          # Child Container Scopes (Phase 14.2.4)
│   ├── dependency_container.py     # Container Resolution Engine (Phase 14.2.3)
│   ├── dependency_graph_analyzer.py# Graph Analysis & Certification (Phase 14.2.5)
│   ├── exceptions.py               # DI Exception Hierarchy (Phase 14.2.1)
│   ├── interfaces.py               # DI ABC Interfaces (Phase 14.2.1)
│   ├── models.py                   # DI Domain Models & Enums (Phase 14.2.1)
│   ├── service_collection.py       # Service Builder API (Phase 14.2.2)
│   └── service_registry.py         # Service Descriptor Registry (Phase 14.2.2)
├── application_provider.py         # Application Runtime Provider (Phase 14.1)
├── application_runtime.py          # Application Lifecycle Manager (Phase 14.1)
├── bootstrap_manager.py            # Bootstrapping & Diagnostics Manager (Phase 14.1)
├── exceptions.py                   # Application Exception Hierarchy (Phase 14.1)
├── initialization_manager.py       # Ordered Component Initializer (Phase 14.1)
├── interfaces.py                   # Application ABC Interfaces (Phase 14.1)
├── models.py                       # Application Domain Models (Phase 14.1)
├── runtime.py                      # Global Lazy Singleton Accessors (Phase 14.1)
├── runtime_registry.py             # Subsystem Runtime Registry (Phase 14.1)
└── startup_validator.py            # Environment & Dependency Validator (Phase 14.1)
```

---

## 2. Key Architecture & Features

### 2.1 Production Application Runtime (Phase 14.1)
- **ApplicationRuntime**: High-level application container coordinating `UNINITIALIZED -> INITIALIZING -> READY -> STOPPING -> STOPPED` lifecycle state machine.
- **RuntimeRegistry**: Registry of active subsystem runtimes.
- **BootstrapManager**: Environment diagnostics and system initialization logging.
- **StartupValidator**: System pre-flight environment checks.

### 2.2 Dependency Injection Subsystem (Phase 14.2)
- **Service Lifetimes**: `SINGLETON` (shared per container), `TRANSIENT` (instantiated per request), `SCOPED` (bound to `ContainerScope` lifetime).
- **ServiceCollection & Registry**: Builder pattern for registering services via implementation types, factory callables, or existing instances.
- **DependencyContainer**: Thread-safe resolution engine with automatic constructor parameter injection and circular dependency detection.
- **DependencyGraphAnalyzer**: Full dependency graph traversal, cycle detection, disorder analysis, and production certification.

### 2.3 Certified Configuration Runtime Subsystem (Phase 14.3)
- **Priority Source Resolution**: `Memory (500) > Environment (400) > DotEnv (300) > Defaults (0)`.
- **Type Conversion Engine**: Automatic conversion for `str`, `int`, `float`, `bool`, `Path`, `list`, `tuple`, `set`, `dict`, `Enum`, and `timedelta`.
- **Constraint Validator**: Validates properties against `min_value`, `max_value`, `min_length`, `max_length`, `regex_pattern`, `allowed_values`, and `required`.
- **Profiles Engine**: Deployment profile management (`development`, `testing`, `production`), parent-child inheritance resolution, and active profile value overrides.
- **Feature Flags Runtime**: Feature flag evaluation with dependency trees, profile restrictions, environment restrictions, and deterministic MD5 rollout percentages.
- **Secrets Management**: In-memory secure `SecretStore`, access policy enforcement (`allow_read`, `allow_write`, `allow_export`), value redaction algorithms (`redact()`), and audit access logging without exposing raw secret strings.
- **Certification Engine**: `ConfigurationCertifier` conducting comprehensive health audits, priority uniqueness validation, diagnostics aggregation, and availability reporting (**100% Availability Certified**).

---

## 3. Thread Safety & Design Standards

- **Thread Safety**: All shared state across stores, registries, managers, providers, and runtimes is protected using `threading.RLock()`.
- **Immutable Domain Models**: All Pydantic v2 models use `ConfigDict(frozen=True)` to prevent unintended runtime mutation.
- **Constructor Dependency Injection**: 100% decoupled components instantiated via explicit parameters.
- **Zero Raw Secret Exposure**: Sensitive configuration values are automatically masked across snapshots, diagnostics, statistics, and log outputs.
