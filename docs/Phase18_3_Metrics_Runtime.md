# Auralis V2 Observability & Operations Runtime
## Phase 18.3 — Metrics Runtime

---

## 1. Objective

Create a clean, provider-independent, strongly-typed Metrics Runtime for application measurement collection and aggregations (Counter, Gauge, Histogram, and Timer) with zero external dependencies.

---

## 2. Architecture

```
MetricsRuntime (thin coordinator, DI support)
        │
        ▼
MetricsProvider (lifecycle, history, statistics, snapshoting)
        │
        ├───────────────────────┐
        ▼                       ▼
MetricsRegistry (metric schemas) Metric Instruments (Counter, Gauge, etc.)
```

**MetricsRuntime** is a thin coordinator delegating execution to the provider.

**MetricsProvider** coordinates instrument creation, validation, rolling sample history tracking, diagnostics, and snapshotting.

**MetricsRegistry** manages registered metric definitions, ensuring uniqueness and preventing collisions.

**Metric Instruments** record values, execute aggregations, and emit samples to the provider.

---

## 3. Directory Structure

```
frontend/src/observability/metrics/
├── models/
│   ├── metric.ts        # MetricType, MetricDefinition
│   ├── sample.ts        # MetricSample
│   ├── snapshot.ts      # MetricSnapshot, aggregations structure
│   ├── statistics.ts    # MetricsStatistics, MetricsDiagnostics
│   └── index.ts         # Models barrel exports
├── interfaces/
│   ├── metric-instrument.ts  # IMetricInstrument, ICounterInstrument...
│   ├── metrics-provider.ts   # IMetricsProvider
│   ├── metrics-runtime.ts    # IMetricsRuntime
│   └── index.ts         # Interfaces barrel exports
├── registry/
│   └── MetricsRegistry.ts
├── provider/
│   ├── CounterMetric.ts
│   ├── GaugeMetric.ts
│   ├── HistogramMetric.ts
│   ├── TimerMetric.ts
│   └── MetricsProvider.ts
├── runtime/
│   └── MetricsRuntime.ts
├── errors/
│   └── MetricsErrors.ts
├── factories/
│   └── metricsFactories.ts
└── index.ts             # Metrics module barrel exports
```

---

## 4. Metric Types

* `COUNTER`: Monotonic increasing value (e.g. total search operations count).
* `GAUGE`: Variable numerical state (e.g. active voice session count).
* `HISTOGRAM`: Numeric observations bucketed aggregations (e.g. file size distributions).
* `TIMER`: Timing duration aggregations (e.g. database query duration).

---

## 5. Metric Definitions

```typescript
export interface MetricDefinition {
  readonly name: string;
  readonly type: MetricTypeValue;
  readonly description?: string;
  readonly unit?: string;
  readonly labelKeys: ReadonlyArray<string>;
  readonly enabled: boolean;
}
```

---

## 6. Labels and Series

We normalise label sets by sorting their keys alphabetically, guaranteeing that order differences do not lead to different series:
`{ op: "search", src: "sidebar" }` and `{ src: "sidebar", op: "search" }` map to the identical series identifier `op=search,src=sidebar`.

---

## 7. Counter

* Starts at 0.
* Only supports positive increases (`increment(value)`).
* Negative values throw `MetricsValidationError`.

---

## 8. Gauge

* Variables that can increase/decrease (`set(value)`, `increment(value)`, `decrement(value)`).
* Rejects NaN and Infinity values.

---

## 9. Histogram

* Configurable buckets sorting ascending (e.g. `[10, 50, 100]`) plus implicit `+Inf` bucket.
* Measures: count, sum, min, max, average.

---

## 10. Timer

* Tracks duration in milliseconds using high-resolution timings `performance.now()` when available.
* Supports start/stop handle callbacks.

---

## 11. Samples

```typescript
export interface MetricSample {
  readonly id: string;
  readonly metricName: string;
  readonly metricType: MetricTypeValue;
  readonly timestamp: number;
  readonly value: number;
  readonly labels?: Record<string, string>;
  readonly seriesKey?: string;
  readonly unit?: string;
  readonly operation?: string;
  readonly durationMs?: number;
}
```

---

## 12. Aggregation

Determined on each observation dynamically:
* `Counter`: sum total.
* `Gauge`: latest set value.
* `Histogram`: bucketing frequency counts plus min/max/average.
* `Timer`: count/sum/min/max/average timings.

---

## 13. History

Tracks recent `MetricSample` objects in an in-memory queue, enforcing FIFO eviction on the history capacity. Samples can be queried by name and labels.

---

## 14. Registry

Ensures unique metric names. Registers metadata definitions and provides O(1) matching metric retrievals.

---

## 15. Statistics

Keeps rollups of registered metrics, sample counts, rejected counts, history sizing, min/max values, and sample timestamps.

---

## 16. Diagnostics

Diagnostics snapshots bundle runtime state, metric and active series counts, rolling statistics summaries, and warning flags.

---

## 17. Lifecycle

Operates: `UNINITIALIZED` $\rightarrow$ `INITIALIZING` $\rightarrow$ `READY` $\rightarrow$ `STOPPING` $\rightarrow$ `STOPPED`.

---

## 18. Dependency Injection

Supports passing constructor arguments mapping custom providers into the coordinator runtime.

---

## 19. Immutability

Public properties (Definitions, Aggregations, Snapshots, Statistics, and Diagnostics) are cloned and frozen recursively using `freezeDeepSafe`.

---

## 20. Error Handling

Enforces early type validation failures (e.g., `MetricAlreadyExistsError`, `MetricNotFoundError`, `MetricsValidationError`).

---

## 21. Performance Targets

* Metric lookup: < 1 ms
* Counter increment: < 1 ms
* Gauge update: < 1 ms
* Histogram observation: < 2 ms
* Timer recording: < 1 ms

---

## 22. Testing Strategy

Validated by 5 test suites under `frontend/tests/observability/metrics/`.

---

## 23. Explicit Boundaries — What Phase 18.3 Does NOT Implement

* ❌ Distributed Tracing (Phase 18.4)
* ❌ Telemetry Exporter (Phase 18.5)
* ❌ Diagnostics Runtime (Phase 18.6)
* ❌ Alerting Runtime (Phase 18.7)
* ❌ Dashboard UI (Phase 18.8)
* ❌ Persistent database storage
* ❌ Remote exporters (Prometheus, OpenTelemetry, Sentry, Datadog)
* ❌ Production certification
