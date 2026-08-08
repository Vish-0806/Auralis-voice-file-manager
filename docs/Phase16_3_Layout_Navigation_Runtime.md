# Phase 16.3 — Layout & Navigation Runtime

This document describes the design, implementation, and quality assertions of the Layout and Navigation Runtime for Auralis Frontend V2.

---

## 1. Objectives
* Establish a responsive, accessible, unified application shell.
* Implement a centralized navigation configuration model as a single source of truth.
* Integrate route-aware dynamic breadcrumbs and page headers.
* Establish nested layout boundaries (Dashboard and Workspace contexts) controlled by the routing hierarchy.
* Guarantee clean separation of concerns between layouts, navigation configuration, and page-specific logic.

---

## 2. Architecture & Design

### Context & Hooks
We introduced a lightweight React Context (`LayoutContext` and `useLayout` hook) inside `AppLayout.tsx` to handle visual layouts, responsive state, and dynamic slots:
* **`isMobileOpen`**: Controls the off-canvas drawer navigation for mobile screens.
* **`isCollapsed`**: Toggle value for collapsing the desktop sidebar to an icon-only format.
* **`actions`**: React Node slot allowing individual page views to dynamically register custom buttons in the global PageHeader.
* **`description`**: Allows page components to set custom page descriptions in the header.

### Rendering Composition Hierarchy
```
React Application (providers.tsx)
       ↓
React Router (routes.tsx)
       ↓
AppLayout (overall shell, TopBar, Sidebar, dynamic PageHeader, Breadcrumbs)
       ↓
Layout Wrapper (DashboardLayout or WorkspaceLayout via <Outlet />)
       ↓
Page Content (DashboardPage, WorkspacePage, etc.)
```

---

## 3. Navigation Configuration

The configuration is centralized inside [navigation.ts](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/app/navigation.ts):
* **`navigationConfig`**: An array mapping navigation items (id, path, icon, labels, sections). Used by the `Sidebar` to render the main menu.
* **`routeMetadataMap`**: Key-value map associating route paths with details like:
  - Header Titles
  - Subtitle Descriptions
  - Breadcrumbs labels
  - Parent path references (for generating crumb hierarchy lists)

---

## 4. Layout & Navigation Hierarchy

The route configuration at [routes.tsx](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/app/routes.tsx) defines the layout wrappers:
* **`AppLayout`**: Outer container wrapping all internal pages.
* **`DashboardLayout`**: Structural wrapper for `/dashboard` index route.
* **`WorkspaceLayout`**: Wrapper for `/workspace` workspace route.

Both sub-layouts dynamically render child components using React Router's `<Outlet />`.

---

## 5. Responsive Strategy
Responsive behavior is handled purely via CSS classes and media queries inside [layout.css](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/styles/layout.css):
* **Desktop**: The sidebar takes `280px` width. When collapsed, width changes to `80px` and text labels hide automatically using CSS.
* **Mobile/Tablet**: The sidebar is fixed off-screen at `left: -280px`. Clicking the menu toggle in `TopBar` activates `.mobile-open` which transitions the sidebar into view. A dark backdrop covers background content.

---

## 6. Accessibility Strategy
* **Semantic Landmarks**: Uses standard HTML elements: `<aside role="complementary">`, `<nav>`, `<header>`, and `<main>`.
* **Screen Reader Announcement**: Active links are declared using `aria-current="page"`. Live/invalid states map correctly using `aria-invalid` and `aria-busy`.
* **Keyboard Focus**: Native links have default tabIndex. CSS styling enforces visible outline highlights on active focus.
* **Aria Labels**: Toggle controls specify meaningful labels (e.g., `aria-label="Toggle Navigation Menu"`).

---

## 7. Testing Strategy
Our tests validate:
1. Shell rendering (`AppLayout`, `TopBar`, `Sidebar`).
2. Toggling mobile menu open/closed.
3. Collapsing sidebar to icon-only mode.
4. Correct layout outlets rendering (`DashboardLayout`, `WorkspaceLayout`).
5. Breadcrumb list traversal matching routing parent keys.
6. Active link color highlighted via `.active` class.

---

## 8. Verification Results
* **TypeScript type checking**: `npm run typecheck` returned `0` errors.
* **Vitest suite**: `npm run test` completed with `30/30` tests passing.
* **Vite build**: `npm run build` compiled successfully.
