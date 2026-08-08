# Phase 16.4 — Theme & Design System Runtime

This document describes the design, implementation, and quality assertions of the Theme & Design System for Auralis Frontend V2.

---

## 1. Objective
Establish a single visual language, design token architecture, and theme preference runtime for Auralis Frontend V2 that integrates seamlessly with Bootstrap, respects user preferences (such as system theme and reduced motion settings), and guarantees color contrast and accessibility.

---

## 2. Design Principles
* **Semantic Tokens**: Components must reference semantic abstractions (e.g. `var(--color-background-subtle)`) rather than raw hex/pixel colors.
* **Non-intrusive Overrides**: Evolve styles by mapping design tokens to Bootstrap's standard utility variable properties (`--bs-body-bg`, etc.) to keep existing layout styles functional.
* **Accessibility First**: Meet minimum AA compliance for colors, maintain focus ring outlines, and respect prefers-reduced-motion triggers.

---

## 3. Token Architecture
Tokens are centralized in [tokens/index.ts](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/theme/tokens/index.ts):
* **Variables Mapping**: Translated to standard CSS Custom Properties in [variables.css](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/src/theme/css/variables.css).
* **Scope**: All tokens are globally available on the `:root` element.

---

## 4. Color System
We define semantic mappings:
* **Backgrounds**: `background`, `backgroundSubtle`, `backgroundElevated`, `backgroundMuted`.
* **Text**: `textPrimary`, `textSecondary`, `textMuted`, `textDisabled`, `textInverse`.
* **Borders**: `border`, `borderSubtle`, `borderStrong`.
* **Brand**: `brand`, `brandHover`, `brandActive`, `brandSubtle`, `brandContrast`.
* **Status**: `success`, `warning`, `danger`, `info` (along with their `Subtle` variants).

---

## 5. Typography System
* **Font Families**: System-sans (`sans`) and Monospace (`mono`).
* **Sizing Scales**: `display` (2.5rem), `h1` (2rem), `h2` (1.5rem), `h3` (1.25rem), `h4` (1.1rem), `bodyLarge` (1.125rem), `body` (1rem), `bodySmall` (0.875rem), `caption` (0.75rem), `label` (0.875rem), `code` (0.875rem).
* **Weights**: `light` (300), `normal` (400), `medium` (500), `semibold` (600), `bold` (700).

---

## 6. Spacing System
Consistent scale mapped to rem values:
* `none` (0), `xs` (0.25rem), `sm` (0.5rem), `md` (1rem), `lg` (1.5rem), `xl` (2rem), `2xl` (3rem), `3xl` (4rem), `4xl` (6rem).

---

## 7. Border & Radius System
* **Radii levels**: `none` (0), `sm` (0.25rem), `md` (0.375rem), `lg` (0.5rem), `xl` (0.75rem), `pill` (50rem), `circle` (50%).

---

## 8. Shadow/Elevation System
* **Elevation levels**: `none`, `sm`, `md`, `lg`, `xl` (resolved to rgba shadows adjusted dynamically between light and dark modes).

---

## 9. Motion System
* **Transitions**: `fast` (150ms), `normal` (250ms), `slow` (350ms).
* **Easings**: `easeIn`, `easeOut`, `easeInOut`, `linear`.
* **Reduced Motion**: Disables transitions and animations globally when `@media (prefers-reduced-motion: reduce)` is matching.

---

## 10. Breakpoints
* Mapped identically to Bootstrap's breakpoints: `xs` (0), `sm` (576px), `md` (768px), `lg` (992px), `xl` (1200px), `xxl` (1400px).

---

## 11. Z-Index Layers
* Centralized scale mapping: `base` (0), `dropdown` (1000), `sticky` (1020), `fixed` (1030), `sidebar` (1040), `modalBackdrop` (1050), `modal` (1060), `toast` (1070), `tooltip` (1080).

---

## 12. Light Theme
Default fallback state. Defined with soft gray background scales (`#f8f9fa`) and high contrast black text (`#212529`).

---

## 13. Dark Theme
Activated via `[data-theme="dark"]` selector. Configured using pure charcoal/dark slate layers to eliminate glare.

---

## 14. System Theme
When theme is set to `system`, the runtime listens to prefers-color-scheme schema changes and applies the resolved mode instantly.

---

## 15. Persistence Strategy
* Mapped to localStorage using key `auralis.theme`.
* Validated on loading: corrupted or unknown storage strings fallback safely to `system` mode.

---

## 16. Bootstrap Integration
* Design tokens are mapped to override standard Bootstrap theme variables: `--bs-body-bg`, `--bs-body-color`, `--bs-border-color`, `--bs-primary`, `--bs-body-bg-rgb`, `--bs-tertiary-bg`, and `--bs-heading-color`.
* Bootstrap components (like cards and forms) dynamically adapt without rewriting.

---

## 17. Accessibility
* High text-to-background contrast ratio (AA compliance).
* Core outlines are preserved for focus-visible elements.
* Visual indicators (icons, labels, and helper texts) accompany all status messages.

---

## 18. Component Integration
* The new design system is integrated with Phase 16.2 components and Phase 16.3 layouts.
* A visual toggle component `<ThemeToggle />` has been added inside the main `TopBar` navbar, cycling between Light, Dark, and System states.

---

## 19. Testing
* Integration suite at [Theme.test.tsx](file:///c:/Users/Vishal%20S%20Naik/MyProjects/Auralis-voice-file-manager/frontend/tests/theme/Theme.test.tsx) validates the provider, toggle cycles, attribute root additions, and listener updates.

---

## 20. Verification Results
* **TypeScript type checking**: `npm run typecheck` returned `0` errors.
* **Vitest suite**: `npm run test` completed with `43/43` tests passing.
* **Vite build**: `npm run build` compiled successfully.

---

## 21. Known Limitations
* Advanced transition properties are globally nullified under prefers-reduced-motion, which can occasionally make drawer animations seem sudden on slow systems.

---

## 22. Future Extension Points
* Theme selector dropdowns in a dedicated settings profile view.
* Custom palette configurations or high-contrast theme variations.
