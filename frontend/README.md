# Auralis Frontend Web Client & Pure TS Runtime Architecture Platform

This directory contains the Vite + React client application and the **Provider-Independent Frontend Architecture & Runtime Platform** (`frontend/src/runtime/`) for the **Auralis Voice File Manager**.

The frontend architecture is designed to be 100% provider-independent, framework-decoupled, thread-safe, and ready for desktop packaging (Electron / Tauri / Native container).

---

## 1. Directory Structure

```
frontend/
├── src/
│   ├── assets/                # App assets and icons
│   ├── components/            # React UI components (Dashboard, Controls, File Viewer)
│   ├── runtime/               # Provider-Independent Frontend Runtime Platform (Phase 16)
│   │   ├── di/                # Dependency Injection Subsystem (Phase 16.1)
│   │   ├── app/               # Application Lifecycle & Plugin Architecture (Phase 16.2)
│   │   ├── config/            # Certified Configuration Runtime Subsystem (Phase 16.3)
│   │   ├── events/            # Provider-Independent Event Runtime Platform (Phase 16.4)
│   │   └── state/             # State Management Runtime Platform (Phase 16.5)
│   ├── App.tsx                # Application root React component
│   ├── main.tsx               # App entry point
│   └── index.css              # Global glassmorphic styling system
├── tests/
│   └── runtime/               # 456 Vitest unit tests across 17 test suites
├── index.html                 # Main HTML document
├── package.json               # Dependencies, scripts, and Vitest configuration
├── tsconfig.json              # TypeScript compilation rules
└── vite.config.ts             # Vite build & Vitest proxy configuration
```

---

## 2. Frontend Subsystem Architecture (Phase 16)

### 2.1 Dependency Injection Subsystem (`frontend/src/runtime/di/`) — Phase 16.1
* **Service Lifetimes**: `SINGLETON`, `TRANSIENT`, `SCOPED`.
* **IoC Container**: `ServiceCollection`, `ServiceDescriptor`, `DependencyContainer`, `ContainerScope`.
* **Dependency Graph Analyzer**: Cycle detection algorithm (`hasCycle()`, `getDependencyGraph()`).
* **Provider & Runtime**: `DependencyProvider`, `DependencyRuntime`, and lazy singleton accessors (`getDependencyRuntime()`, `getDependencyProvider()`).

### 2.2 Application Lifecycle & Plugin Architecture (`frontend/src/runtime/app/`) — Phase 16.2
* **Lifecycle State Machine**: `UNINITIALIZED` → `INITIALIZING` → `READY` → `STOPPING` → `STOPPED`.
* **Bootstrap & Validation**: `RuntimeRegistry`, `BootstrapManager`, `StartupValidator`, `InitializationManager`.
* **Plugin Platform**: `PluginEngine` supporting dynamic plugin registration, lifecycle hooks, and dependency verification.
* **App Coordinator**: `ApplicationProvider`, `ApplicationRuntime`, and lazy singleton accessors (`getApplicationRuntime()`, `getApplicationProvider()`).

### 2.3 Certified Configuration Subsystem (`frontend/src/runtime/config/`) — Phase 16.3
* **Multi-Source Priority Resolver**: `Memory (500) > Environment (400) > DotEnv (300) > Defaults (0)`.
* **Type Resolver & Validation**: `ConfigurationResolver` (automatic type casting) and `ConfigurationValidator` (constraint verification).
* **Profiles & Feature Flags**: Profile inheritance (`development`, `testing`, `production`), active profile switching, feature flags, and deterministic MD5 rollout percentages.
* **Secret Management**: Thread-safe in-memory `SecretStore`, access policies (`allow_read`, `allow_write`, `allow_export`), value redaction algorithms (`redact()`), and audit access logging.
* **Production Certification**: `ConfigurationCertifier` executing 10 verification checks with 100/100 score.

### 2.4 Provider-Independent Event Runtime Architecture Platform (`frontend/src/runtime/events/`) — Phase 16.4
* **Event Bus & Registries**: `EventBus`, `EventRegistry` (type validation), `SubscriberRegistry` (sorted subscriptions).
* **Subscription Management**: `SubscriptionManager` with strict try/catch exception isolation per handler callback.
* **Topic Routing & Filtering Engine**: `EventRouter` supporting exact match, single-level wildcard `*`, multi-level wildcard `**` / `#`, predicate filtering, and priority rule ordering (`CRITICAL > HIGH > NORMAL > LOW`).
* **Dispatch Manager & Dead Letters**: `DispatchManager` controlling dispatch execution and dead-letter creation for failed subscribers.
* **Asynchronous Priority Event Queue**: `EventQueue` bounded priority queue (capacity 1000) with `DROP_OLDEST` overflow strategy.
* **Retry & Replay Engines**: `RetryManager` (exponential attempt tracking) and `ReplayManager` (historical set and filtered replaying).
* **Production Certification**: `EventCertifier` executing 10 verification checks with 100/100 score.

### 2.5 State Management Runtime Platform (`frontend/src/runtime/state/`) — Phase 16.5
* **State Containers & Store**: `StateContainerEngine` providing deep immutability (`Object.freeze()`), container mutation operations (setState, replaceState, mergeState, resetState, cloneState, freezeState), and `StateStore` managing multiple named containers.
* **State Registry & Actions**: `StateRegistry` (container discovery & duplicate detection) and `ActionDispatcher` (sync/async action pipeline, priorities, history logging).
* **Reducers & Middleware**: `ReducerEngine` (pure reducers, ordered execution, exception isolation) and `MiddlewareManager` (`BEFORE`, `AFTER`, `ERROR` hooks).
* **Selectors & Memoization**: `SelectorEngine` supporting memoized and derived selectors, state dependency tracking, and cache invalidation.
* **Undo / Redo History Engine**: `HistoryManager` and `UndoRedoManager` supporting snapshot timeline logging, history capacity limits, and time travel state restoration.
* **Persistence & Synchronization**: `PersistenceManager` (abstract versioned saving & loading) and `StateSynchronizer` (conflict detection & version diffing).
* **Production Certification**: `StateCertifier` executing 10 verification checks with 100/100 score.

---

## 3. Getting Started

### Installation
Ensure Node.js (v18+) is installed:
```bash
cd frontend
npm install
```

### Running Development Server
Launch Vite dev server:
```bash
npm run dev
```
Access the application dashboard at `http://localhost:5173`.

### Running Tests
Execute the Vitest unit test suite:
```bash
npm test
```
Runs all **456 unit tests across 17 test suites** verifying DI, Application Lifecycle, Configuration, Events, State Management, and Production Certification.

### Production Build
Compile production assets:
```bash
npm run build
```
Generates production bundle in `dist/` in ~4 seconds.
