# Auralis V2 Observability & Operations Runtime
## Phase 18.4 — Distributed Tracing Runtime

---

## 1. Objective

Create a provider-independent, strongly-typed Distributed Tracing Runtime capable of creating traces and spans, maintaining parent-child relationships, propagating trace context, recording span attributes/events/errors, managing in-memory trace history, and exposing the functionality through a thin DI coordinator with zero external dependencies.

---

## 2. Architecture

```
TracingRuntime (DI Coordinator)
        │
        ▼
TracingProvider (Lifecycle, active collections, history capacity)
        │
        ├───────────────────────┐
        ▼                       ▼
TracingRegistry (Trace/Span indices) SpanImpl (attributes, events, timing)
```

**TracingRuntime** acts as a thin coordinator forwarding execution calls to the injected or default `TracingProvider` delegate.

**TracingProvider** orchestrates the active collections, lifecycle states, trace history queue, statistics compilation, and diagnostic snapshot generation.

**TracingRegistry** caches registered trace nodes and active/completed spans, facilitating O(1) matching parent-child searches and cascading removals.

**SpanImpl** is the concrete implementation of the span handle (`ISpan`), executing attribute modifications, error logging, and timing duration tracking.

---

## 3. Directory Structure

```
frontend/src/observability/tracing/
├── models/
│   ├── trace.ts        # Trace definition interface
│   ├── span.ts         # Span, SpanKind, SpanStatus definitions
│   ├── context.ts      # TraceContext interface
│   ├── event.ts        # SpanEvent interface
│   ├── statistics.ts    # TracingStatistics, TracingDiagnostics
│   └── index.ts         # Models barrel exports
├── interfaces/
│   ├── span.ts         # ISpan interface
│   ├── tracing-provider.ts  # ITracingProvider interface
│   ├── tracing-runtime.ts   # ITracingRuntime interface
│   └── index.ts         # Interfaces barrel exports
├── registry/
│   └── TracingRegistry.ts   # private Maps trace-spans tree indexer
├── provider/
│   ├── Span.ts         # SpanImpl handle execution
│   └── TracingProvider.ts   # Tracing provider lifecycle and actions
├── runtime/
│   └── TracingRuntime.ts    # Coordinator delegation wrapper
├── errors/
│   └── TracingErrors.ts     # TracingRuntimeError, SpanNotFoundError...
├── factories/
│   └── tracingFactories.ts  # Hex ID generators and schemas checking
└── index.ts             # Tracing module barrel exports
```

---

## 4. Domain Models

### Trace
Encapsulates trace identity, timing, health status, and metadata:
* `traceId`: hexadecimal identifier
* `name`: trace transaction name
* `startTime`: start timestamp
* `endTime`: end timestamp
* `duration`: elapsed duration
* `rootSpanId`: root span identifier
* `status`: resolved trace health status
* `metadata`: tracing metadata records
* `spansCount`: count of registered spans in this trace tree

### Span
Tracks single execution segment boundaries:
* `spanId`: span identifier
* `traceId`: parent trace identifier
* `parentSpanId`: parent span identifier
* `name`: execution segment name
* `kind`: `INTERNAL` | `SERVER` | `CLIENT` | `PRODUCER` | `CONSUMER`
* `startTime`: start timestamp
* `endTime`: end timestamp
* `duration`: elapsed duration
* `status`: `UNSET` | `OK` | `ERROR`
* `attributes`: key-value metadata logs
* `events`: list of custom events recorded
* `error`: normalized error fields

---

## 5. Trace Lifecycle

A trace is initiated using `startTrace(name, options?)`, generating a unique trace ID and creating the root span. The trace transitions its status from `UNSET` to `OK` or `ERROR` based on the status of its constituent spans. A trace is marked completed when its root span is ended.

---

## 6. Span Lifecycle

Spans transition through a simple lifecycle:
1. **Start**: Created via `startTrace` or `startSpan`, recording the start time.
2. **Operations**: Setting attributes, appending events, or recording errors while active.
3. **End**: Invoking `end()` calculates the duration and notifies the provider to update diagnostics. Double completion is protected and throws `SpanStateError`.

---

## 7. Parent-Child Relationships

Child spans are created via `startSpan(name, options)` by linking them using `parentSpanId` to their parent span. The parent span and trace context must exist in the registry, ensuring trace integrity.

---

## 8. Context Propagation

Context is propagated out-of-band using the following methods:
* `createContext(span)`: generates a `TraceContext` from an active span.
* `extractContext(context)`: extracts the parent context identifiers.
* `injectContext(context)`: propagates context to link subsequent span transactions.

---

## 9. Attributes, Events, and Errors

* **Attributes**: Key-value pairs constrained to serializable primitive types.
* **Events**: Named snapshots capturing a timestamp and attributes.
* **Errors**: Normalized into a safe `StructuredError` data structure to prevent raw error references from leaking. Spans are automatically set to `ERROR` when recording an error.

---

## 10. History Queue

Tracing history is stored in an in-memory queue capped at a capacity of 100 traces. When capacity is exceeded, oldest completed traces are evicted first (FIFO) to preserve active traces.

---

## 11. Statistics

Includes rollups for started/completed/active/error traces and spans, total and average durations, and event counts.

---

## 12. Diagnostics

Local diagnostics snapshots provide details on runtime lifecycle state, statistics, trace counts, active counts, capacity limits, and generation timestamps.

---

## 13. Dependency Injection

Coordinator classes support injecting mock or alternative tracing provider implementations.

---

## 14. Immutability

Public objects (Traces, Spans, Snapshots, Statistics, and Diagnostics) are cloned and recursively frozen using `freezeDeepSafe`.

---

## 15. Testing

Verified by 23 tests across 5 files:
* `tracing_runtime.test.ts`: lifecycle, coordinator delegation, DI checks.
* `tracing_provider.test.ts`: trace/span creation, statistics, FIFO history eviction checks.
* `tracing_registry.test.ts`: tree index maps, cascading removals checks.
* `tracing_spans.test.ts`: attribute validations, events serialization, error mapping, double complete checks.
* `tracing_context.test.ts`: context propagation and parent linkages checks.

---

## 16. Performance Measurements

* Trace initiation: < 1 ms
* Span creation: < 1 ms
* Span ending: < 1 ms
* Diagnostics snaps: < 1 ms

---

## 17. Known Limitations

* Bounded in-memory history only.
* No persistence storage or file logs.

---

## 18. Explicit Phase 18.4 Boundaries — What is NOT Implemented

* ❌ OpenTelemetry / Jaeger / Zipkin
* ❌ HTTP / remote tracing exporters
* ❌ persistent database backend storage
* ❌ alerts or dashboard visualizations
* ❌ Phase 18.5+ telemetry pipelines
