# Auralis V2 Observability & Operations Runtime
## Phase 18.2 — Logging Runtime

---

## 1. Objective

Create a clean, provider-independent, strongly-typed structured Logging Runtime for Auralis that handles structured log records, log levels, configurations, sinks, deterministic filtering, and bounded log history with no external runtime dependencies.

---

## 2. Architecture

```
LoggingRuntime (thin coordinator, DI support)
        │
        ▼
LoggingProvider (lifecycle, dispatch, history, statistics)
        │
        ├───────────────────────┐
        ▼                       ▼
LoggingRegistry (loggers)  Log Sinks (e.g. InMemoryLogSink)
```

**LoggingRuntime** is a thin delegation layer forwarding every request to the provider.

**LoggingProvider** coordinates logger registries, sink registrations, and log execution (creating records, processing context, applying filtering, maintaining rolling history/statistics).

**LoggingRegistry** manages loggers and configurations, ensuring name uniqueness and lazy initialization.

**Log Sinks** are custom dispatch targets receiving formatted, frozen log records.

---

## 3. Directory Structure

```
frontend/src/observability/logging/
├── models/
│   ├── log.ts            # LogLevel, StructuredError, LogRecord
│   ├── logger.ts         # LogContext, LogOptions
│   ├── sink.ts           # LogSinkStatistics
│   ├── statistics.ts     # LoggingStatistics, LoggingDiagnostics
│   └── index.ts          # Barrel exports
├── interfaces/
│   ├── logger.ts         # ILogger
│   ├── log-sink.ts       # ILogSink
│   ├── logging-provider.ts
│   ├── logging-runtime.ts
│   └── index.ts          # Barrel exports
├── registry/
│   └── LoggingRegistry.ts
├── provider/
│   ├── Logger.ts         # ILogger class implementation
│   └── LoggingProvider.ts
├── runtime/
│   └── LoggingRuntime.ts
├── sinks/
│   ├── InMemoryLogSink.ts
│   └── index.ts          # Barrel exports
├── errors/
│   └── LoggingErrors.ts
├── factories/
│   └── loggingFactories.ts
└── index.ts              # Logging barrel exports
```

---

## 4. Log Levels

| Log Level | Severity | Purpose |
|---|---|---|
| `TRACE` | 0 | Extremely detailed/fine-grained execution diagnostics |
| `DEBUG` | 1 | Standard developer debugging logs |
| `INFO` | 2 | Important operational runtime events |
| `WARN` | 3 | Potential runtime issues, non-fatal errors |
| `ERROR` | 4 | Recoverable runtime failures |
| `FATAL` | 5 | Critical crashes |

We enforce:
`TRACE` < `DEBUG` < `INFO` < `WARN` < `ERROR` < `FATAL`

---

## 5. Log Record Structure

```typescript
export interface LogRecord {
  readonly id: string;
  readonly timestamp: number;
  readonly level: LogLevelValue;
  readonly message: string;
  readonly loggerName: string;
  readonly context?: Record<string, unknown>;
  readonly metadata?: Record<string, unknown>;
  readonly error?: StructuredError;
  readonly correlationId?: string;
  readonly requestId?: string;
  readonly sessionId?: string;
  readonly pluginId?: string;
  readonly componentId?: string;
  readonly operation?: string;
  readonly durationMs?: number;
}
```

---

## 6. Logger API

Supports the following overloaded methods:
* `trace(message, metadata?, context?)` or `trace(message, options?)`
* `debug(message, metadata?, context?)` or `debug(message, options?)`
* `info(message, metadata?, context?)` or `info(message, options?)`
* `warn(message, metadata?, context?)` or `warn(message, options?)`
* `error(message, error?, metadata?)` or `error(message, options?)`
* `fatal(message, error?, metadata?)` or `fatal(message, options?)`

---

## 7. Context Propagation

Callers can create child loggers carrying additional context via:
```typescript
const childLogger = parentLogger.child({ requestId: "req-123" });
```
This inherits parent configurations, copies and freezes the merged context recursively, and prevents any parent mutation.

---

## 8. Registry

* Manages registered configs and mapped `ILogger` instances.
* Lazy retrieval via `getLogger(name)` creates config and logger instance if not present.
* Duplicate config registration throws `LoggingRegistrationError`.

---

## 9. Sink Abstraction

Sinks implement `ILogSink` and handle asynchronous/synchronous writes.
```typescript
export interface ILogSink {
  readonly id: string;
  readonly name: string;
  isEnabled(): boolean;
  setEnabled(enabled: boolean): void;
  getMinLevel(): LogLevelValue;
  setMinLevel(level: LogLevelValue): void;
  write(record: LogRecord): Promise<void>;
  flush(): Promise<void>;
  close(): Promise<void>;
  getStatistics(): LogSinkStatistics;
}
```

---

## 10. In-Memory Sink

`InMemoryLogSink` keeps a bounded FIFO ring buffer of logging records in memory, throwing out the oldest items once capacity is hit. Useful for diagnostics, tests, and future dashboards.

---

## 11. Filtering

Determined sequentially:
1. **Global Provider Level Check**: If log record severity is below global min level, it is filtered.
2. **Logger Level Check**: If log record severity is below logger configuration's level threshold, it is filtered.
3. **Sink Level Check**: Each sink compares record severity against its own minimum level before accepting.

---

## 12. Log History

`LoggingProvider` maintains a thread-safe, bounded, in-memory array of recent records (`getRecentLogs(limit?)`), which can be queried by level, logger name, and correlation identifier.

---

## 13. Statistics

Tracks rollups of:
* Log level counts (`infoCount`, `warnCount`, etc.)
* Filtered logs count (`filteredCount`)
* Dispatch counts and failed sink write metrics (`failedSinkWrites`)

---

## 14. Lifecycle

State transitions:
```
UNINITIALIZED → INITIALIZING → READY → STOPPING → STOPPED
```
Shutdown flushes and closes all registered sinks correctly. Invalid transitions throw `LoggingStateError`.

---

## 15. Diagnostics

`getDiagnostics()` returns a deep-frozen snapshot detailing state, counts, rolled statistics, and potential warnings (e.g. sink write failures).

---

## 16. Error Handling

When errors are logged, they are structured safely (name, message, stack, code, cause) to avoid circular references and JSON stringification failures.
Sinks are fully isolated: if a sink's write function fails or rejects, it increments the provider's `failedSinkWrites` statistic but does NOT crash the active logger call.

---

## 17. Security Considerations

We do NOT capture or serialize arbitrary sensitive data (such as headers, passwords, cookies, or authorization tokens) automatically. Callers are responsible for not explicitly logging secrets.

---

## 18. Immutability

Public outputs are deep-frozen utilizing the Phase 18.1 `freezeDeepSafe` utility to prevent consumers from mutating the provider state.

---

## 19. Dependency Injection

Provides constructor injection of `ILoggingProvider` into `LoggingRuntime`.

---

## 20. Performance Targets

* Logger lookup: < 1 ms
* Log record creation: < 1 ms
* In-memory sink write: < 1 ms
* Simple filtering: < 1 ms

---

## 21. Testing Strategy

Covered extensively by 4 test files:
1. `logging_runtime.test.ts`
2. `logging_provider.test.ts`
3. `logging_registry.test.ts`
4. `logging_sinks.test.ts`

---

## 22. Explicit Boundaries — What Phase 18.2 Does NOT Implement

* ❌ Metrics Runtime (Phase 18.3)
* ❌ Distributed Tracing (Phase 18.4)
* ❌ Telemetry Runtime (Phase 18.5)
* ❌ Diagnostics Runtime (Phase 18.6)
* ❌ Alerting Runtime (Phase 18.7)
* ❌ Dashboard UI (Phase 18.8)
* ❌ Persistent / Filesystem log storage
* ❌ Remote log shipping
* ❌ OpenTelemetry / Prometheus / Sentry integrations
* ❌ Production certification
