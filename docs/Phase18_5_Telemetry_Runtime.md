# Auralis V2 Observability & Operations Runtime
## Phase 18.5 — Telemetry Runtime

---

## 1. Objective

Create a provider-independent, strongly-typed Telemetry Runtime responsible for collecting, normalizing, batching, buffering, and exporting telemetry records with deterministic sampling and retry logic with zero external dependencies.

---

## 2. Architecture

```
TelemetryRuntime (DI Coordinator)
        │
        ▼
TelemetryProvider (Sampling config, stats, diagnostics, flush)
        │
        ├───────────────────────┬───────────────────────┐
        ▼                       ▼                       ▼
TelemetryRegistry (Exporters) TelemetryBuffer (FIFO) InMemoryTelemetryExporter
```

**TelemetryRuntime** acts as a thin DI coordinator delegating execution calls to the provider.

**TelemetryProvider** orchestrates ingestion, validation, credential redaction, sampling decisions, batch grouping, retry loops, statistics, and diagnostics.

**TelemetryRegistry** manages exporter configurations, guaranteeing uniqueness and O(1) searches.

**TelemetryBuffer** is a bounded FIFO memory buffer that handles capacity constraints and counts overflows.

**InMemoryTelemetryExporter** implements `ITelemetryExporter` for testing and simulated fail scenarios.

---

## 3. Directory Structure

```
frontend/src/observability/telemetry/
├── models/
│   ├── telemetry.ts     # TelemetryRecord, TelemetryType, Severity
│   ├── event.ts         # TelemetryEventRecord
│   ├── batch.ts         # TelemetryBatch interface
│   ├── export.ts        # TelemetryExportResult interface
│   ├── sampling.ts      # SamplingConfig interface
│   ├── statistics.ts    # TelemetryStatistics, TelemetryDiagnostics
│   └── index.ts         # Models barrel exports
├── interfaces/
│   ├── telemetry-exporter.ts # ITelemetryExporter
│   ├── telemetry-provider.ts # ITelemetryProvider
│   ├── telemetry-runtime.ts  # ITelemetryRuntime
│   └── index.ts         # Interfaces barrel exports
├── registry/
│   └── TelemetryRegistry.ts # private Map registry for exporters
├── buffer/
│   └── TelemetryBuffer.ts   # bounded FIFO array buffer
├── exporters/
│   ├── InMemoryTelemetryExporter.ts # test mock exporter
│   └── index.ts         # Exporters barrel exports
├── provider/
│   └── TelemetryProvider.ts # telemetry provider business engine
├── runtime/
│   └── TelemetryRuntime.ts  # coordinator coordinator delegate
├── errors/
│   └── TelemetryErrors.ts   # TelemetryRuntimeError, TelemetryStateError...
├── factories/
│   └── telemetryFactories.ts # hashing sampler and field schema checkers
└── index.ts             # Telemetry module barrel exports
```

---

## 4. Domain Models

* `TelemetryRecord`: Encapsulates id, timestamp, type (`LOG`, `METRIC`, `TRACE`, `EVENT`, `CUSTOM`), source, name, severity (`DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL`), attributes, and metadata.
* `TelemetryBatch`: Bundles records for dispatch containing batchId, recordCount, and size.
* `TelemetryExportResult`: Exposes success/failure flags, attempted/failed record counts, duration, and error fields.
* `TelemetryStatistics`: Exposes counts for accepted, rejected, sampled, buffered, evicted, exported, and failed records, and retry attempts.
* `TelemetryDiagnostics`: Bundles state, capacity, buffer sizes, and statistics.

---

## 5. Telemetry Registry

Stores registered exporters dynamically in a private Map, enforcing name uniqueness. O(1) lookups return frozen definitions.

---

## 6. Telemetry Buffer

Configurable maximum capacity (FIFO) that ejects oldest records when capacity is exceeded to prevent unbounded memory growth. Supports prepending failed retries.

---

## 7. Sampling

Deterministic hashing function of the record ID evaluates decisions between 0.0 (drop) and 1.0 (keep all). ERROR and FATAL records bypass sampling and are always preserved.

---

## 8. Batching

Batches records up to `maxBatchRecords = 50`. Ingesting records triggers auto-flush when capacity is reached.

---

## 9. Export Pipeline

Asynchronously sends batch records to enabled exporters. Exporter failures are isolated and do not crash the telemetry module.

---

## 10. Retry Policy

Bounded retry configuration allows retrying a batch up to 3 times on exporter failure, tracking retry stats.

---

## 11. Lifecycle

Transitions: `UNINITIALIZED` $\rightarrow$ `INITIALIZING` $\rightarrow$ `READY` $\rightarrow$ `FLUSHING` $\rightarrow$ `STOPPING` $\rightarrow$ `STOPPED`. Shutdown triggers a final buffer flush.

---

## 12. Immutability

Clones and deep freezes definitions, batches, statistics, and diagnostics using `freezeDeepSafe`.

---

## 13. Dependency Injection

Coordinator runtime accepts alternative custom provider mock injections.

---

## 14. Testing

Verified by 22 tests across 6 files:
* `telemetry_runtime.test.ts`: lifecycle operations and DI coordinator delegation.
* `telemetry_provider.test.ts`: record validations, convenience recorders, credential redacting.
* `telemetry_registry.test.ts`: exporter registrations and name collision protections.
* `telemetry_buffer.test.ts`: FIFO enqueuing, capacity overflow evictions.
* `telemetry_sampling.test.ts`: hashing deterministic decisions, ERROR bypass.
* `telemetry_export.test.ts`: batch sends, retry counts, exporter isolation.

---

## 15. Performance Measurements

* Record validation and cleaning: < 1 ms
* Buffer enqueuing and evictions: < 1 ms
* Batch creation and exports: < 2 ms

---

## 16. Known Limitations

* Bounded in-memory telemetry records only.
* No persistence database or network transmission.

---

## 17. Explicit Phase 18.5 Boundaries — What is NOT Implemented

* ❌ Phase 18.6 Diagnostics Runtime
* ❌ Phase 18.7 Alerting subsystem
* ❌ Phase 18.8 Visual Dashboard
* ❌ OpenTelemetry / HTTP remote exporters
* ❌ database or file persistence storage
* ❌ browser telemetry hooks
