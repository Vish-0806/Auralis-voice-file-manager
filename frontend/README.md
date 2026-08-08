# Auralis Frontend V2

A clean, scalable, production-oriented React + TypeScript architecture built on Vite.

## Core Stack
- **UI & Views:** React, React Router, Bootstrap, Bootstrap Icons
- **HTTP Client:** Axios
- **Test Runner:** Vitest, jsdom, React Testing Library
- **Build System:** Vite, TypeScript

---

## Current Status
**Phase 16.1 — Frontend Runtime Foundation** is the current architectural foundation.

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

## Development Commands

*   `npm run dev` – Launch local hot-reload dev server.
*   `npm run build` – Run type checking and build production bundle.
*   `npm test` – Execute test suite once.
*   `npm run test:watch` – Start Vitest file watcher.
*   `npm run typecheck` – Run strict TypeScript compiler assertions.
*   `npm run preview` – Serve production bundle locally.
