# Phase 16.5 — State Management Runtime

This document describes the design, implementation, and quality assertions of the State Management system for Auralis Frontend V2.

---

## 1. Objective
Establish a clean, lightweight, strongly typed global state management architecture for Frontend V2 that separates state and side-effects from visual components, avoids re-renders via narrow selectors, supports selective localStorage persistence, and avoids legacy overengineering (e.g. custom certifiers or container registries).

---

## 2. Architecture
Built entirely on **Zustand**, leveraging its React-hooks integration and standard pub/sub mechanisms:
```
           React Components
                  │
                  ▼ (Hook Subscriptions)
         Selectors / Actions
                  │
                  ▼
              Zustand Store
                  │
                  ▼ (Middleware)
         localStorage Cache
```

---

## 3. State Boundaries
We define five separate stores corresponding to functional feature zones:
* **UI State**: Manages sidebars, layout collapses, modal triggers, and loading states.
* **Assistant State**: Tracks conversation sessions, messages, streaming indicators, and request statuses.
* **Files State**: Tracks paths, selection targets, sorting options, and view configurations.
* **Workspace State**: Coordinates panels, staging regions, and active editor tabs.
* **Settings State**: Configures preferences like layout density and accessibility adjustments.

---

## 4. UI State
Exposes sidebar control flags. Integrated directly to replace local states with global state models:
```typescript
interface UIState {
  sidebarCollapsed: boolean;
  mobileNavigationOpen: boolean;
  activeModal: string | null;
  globalLoading: boolean;
}
```

---

## 5. Assistant State
Tracks conversation history structures:
```typescript
interface AssistantMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
}
```

---

## 6. Files State
Manages manager lists and options:
```typescript
interface FilesState {
  currentDirectory: string;
  selectedFileIds: string[];
  searchQuery: string;
  sortMode: 'name' | 'date' | 'size';
  sortDirection: 'asc' | 'desc';
  viewMode: 'grid' | 'list';
}
```

---

## 7. Workspace State
Coordinates panels:
```typescript
interface WorkspaceState {
  activeWorkspaceId: string | null;
  openPanels: string[];
  activeTab: string | null;
}
```

---

## 8. Settings State
Configuration properties:
```typescript
interface SettingsState {
  uiDensity: 'compact' | 'normal' | 'cozy';
  accessibilityPreference: {
    highContrast: boolean;
    screenReaderOptimized: boolean;
  };
}
```

---

## 9. Store Structure
Stores are defined using Zustand's `create` hook. No class wrappers or provider boilerplate is required.

---

## 10. Action Conventions
All store updates occur via typed methods bound directly inside the store object (e.g. `setSidebarCollapsed(value)`, `toggleFileSelection(id)`), ensuring actions are predictable and easily auditable.

---

## 11. Selector Conventions
Components subscribe only to required fields via narrow selector functions (e.g. `const density = useSettingsStore(selectUiDensity)`). This prevents unnecessary rendering sweeps when unrelated variables change.

---

## 12. Persistence
Using Zustand's built-in `persist` middleware, keys are versioned and stored under domain names (e.g. `auralis.ui`, `auralis.settings`). Unrecognized or corrupt values fallback safely to defaults during initialization.

---

## 13. Security Rules
* **No Secrets**: Never cache passwords, authentication tokens, API keys, or private variables in store states or persistence layers.
* **Transient Memory**: Sensitive session states remain strictly in volatile memory.

---

## 14. React Integration
Driven by custom selector hooks:
```typescript
const collapsed = useUIStore(selectSidebarCollapsed);
```

---

## 15. Layout Integration
Integrated directly inside `AppLayout.tsx`. Ephemeral drawer views (`isMobileOpen`) remain in local layout state, while the persistent `isCollapsed` setting is read and toggled using the global `useUIStore` hook.

---

## 16. Testing Strategy
* **Integration Tests**: Tests at [State.test.tsx](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/tests/state/State.test.tsx) validate initial state setups, mutations, resets, selectors, local persistence saves, and React component renders.

---

## 17. Performance Considerations
* No global "mega-stores". Feature states are isolated in distinct smaller slices.
* State selection is optimized using selectors to avoid component updates when unrelated values change.

---

## 18. Known Limitations
* Persistence operations are synchronous via localStorage. Avoid caching large arrays or complex objects to prevent blocking the main thread.

---

## 19. Future Extension Points
* Custom state synchronizers mapping store settings to user configuration profiles on the server.
