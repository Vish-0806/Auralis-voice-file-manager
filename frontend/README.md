# Auralis Frontend V2

A clean, scalable, production-oriented React + TypeScript architecture built on Vite.

## Core Stack
- **UI & Views:** React, React Router, Bootstrap, Bootstrap Icons
- **HTTP Client:** Axios
- **Test Runner:** Vitest, jsdom, React Testing Library
- **Build System:** Vite, TypeScript

---

## Current Status
**Phases 16.1 to 16.6 — Core Frontend V2 Stack** is fully complete. This includes the Component Runtime, Layout & Navigation, Theme & Design Tokens system, global Zustand state store boundaries, Axios API client, in-memory AuthService, WebSocket client, and Synchronization bridge.

---

## Directory Structure & Responsibilities

*   `src/app/` – App boot, global route registry, provider wrappers. No feature logic.
*   `src/components/` – Presentation-oriented reusable UI widgets.
*   `src/pages/` – Route-level screen components composing layouts, state, and services.
*   `src/layouts/` – Shell configurations for overall, workspace, and dashboard views.
*   `src/features/` – Isolated feature slices containing specific components, hooks, or assets.
*   `src/services/` – External communications (API, Authentication, WebSockets, State Synchronization).
*   `src/state/` – Storage boundaries for application state (Stores, Selectors, Types).
*   `src/theme/` – Structural foundation for light/dark theme providers.
*   `src/voice/` – Interface layers for future microphone & speech runtimes.
*   `src/config/` – Typed environmental boundaries.

---

## Component Architecture

Auralis Frontend V2 component architecture is designed to be highly reusable, accessible, type-safe, and visually consistent. Components are structured hierarchically under `@/components/`:

### Reusable Component Groups

1. **Common Components (`src/components/common/`)**
   - Pure presentational elements that do not contain application state or business logic.
   - Includes: `Button`, `IconButton`, `Input`, `Textarea`, `Select`, `Checkbox`, `Switch`, `Card`, `Badge`, `Avatar`, `Divider`, `Tooltip`, `Modal`, `Dropdown`, `Tabs`, `Spinner`, `Progress`, `Alert`, `Toast`, `EmptyState`, `ErrorState`, and `Skeleton`.

2. **Layout Components (`src/components/layout/`)**
   - Flexbox and Grid composition helpers based on Bootstrap structures.
   - Includes: `Stack` (flex direction alignment), `Row` (grid rows), `Container` (grid layout content centering), `Section` (semantic padding layouts), and `Panel` (bordered/shadowed content sections).

3. **Navigation Components (`src/components/navigation/`)**
   - Structural navigation primitives integrated with React Router.
   - Includes: `NavItem` (routing links), `Sidebar` (menu sidebar panels), `TopBar` (nav headers), `Breadcrumbs` (historical context), and `PageHeader` (page headers with descriptions and main actions).

### Component Testing Strategy
- Tests are organized under `tests/components/` (divided into `common/`, `layout/`, and `navigation/`).
- Focuses on testing functional behavior, accessibility states, and semantic output:
  - **Button**: Verify render, click behavior, disabled, and busy loading states.
  - **Input**: Verify label relationship, validation states (`is-invalid`), and change triggers.
  - **Modal**: Verify display lifecycle, Esc key and backdrop close handlers, and dialog roles.
  - **Tabs**: Verify tab selection transitions and active tab panel rendering.

### Accessibility Principles
- **Semantic HTML**: Proper use of native tags (`button`, `input`, `aside`, `nav`, etc.) to provide natural screen reader indicators.
- **ARIA Roles & States**: Appropriate mapping of roles (`role="dialog"`, `role="tab"`) and live/invalid states (`aria-invalid`, `aria-describedby`, `aria-busy`, `aria-selected`).
- **Keyboard Access**: Focus trapping inside modal screens, keyboard Esc key handling, and natural tab focus indexing for all custom controls.
- **Accessibly Named Elements**: Mandatory labels for form controls (`Input`, `Select`) and explicit `aria-label` definitions for icon-only actions (`IconButton`).

---

## Development Commands

*   `npm run dev` – Launch local hot-reload dev server.
*   `npm run build` – Run type checking and build production bundle.
*   `npm test` – Execute test suite once.
*   `npm run test:watch` – Start Vitest file watcher.
*   `npm run typecheck` – Run strict TypeScript compiler assertions.
*   `npm run preview` – Serve production bundle locally.
