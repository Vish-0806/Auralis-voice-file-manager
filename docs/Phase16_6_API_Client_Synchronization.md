# Phase 16.6 — API Client & Synchronization Runtime

This document describes the design, implementation, and quality assertions of the API Client and WebSocket Synchronization system for Auralis Frontend V2.

---

## 1. Objective
Establish a centralized, type-safe API client (Axios-based) and WebSocket listener coordinate to handle communications between the React frontend, Zustand stores, and FastAPI backend.

---

## 2. API Client Architecture
Driven by a single, configured `ApiClient` instance that reads the backend host dynamically:
```
           React Components / Pages
                       │
                       ▼
                 Domain Services
                       │
                       ▼
                   ApiClient
                       │
                       ▼ (Request Interceptors)
             Authorization Header
                       │
                       ▼ (Response Interceptors)
             AuralisApiError Normalizer
```

---

## 3. Environment Variables
System parameters are configurable through Vite environment files:
* `VITE_API_BASE_URL`: Root path of the FastAPI application. Defaults to `http://localhost:8000`.
* `VITE_WS_URL`: WebSocket endpoint of the FastAPI application. Defaults to `ws://localhost:8000/ws`.

---

## 4. Authentication Boundary
* **Memory Session Store**: Since the backend currently contains no active authentication schema, `AuthService` handles memory-only placeholders.
* **Header Injection**: Requests are intercepted dynamically to attach `Authorization: Bearer <token>` if a session is present.

---

## 5. WebSocket Architecture
* **Connection Coordinator**: Driven by `WebSocketClient`, managing connections independently from React or Zustand.
* **Failover Resilience**: Connection failures trigger automatic reconnection loops with exponential backoff (e.g. 50ms, 100ms, 200ms).
* **Memory Protection**: Listeners are tracked using standard `Set` collections and provide unsubscribe callbacks to prevent leaks.

---

## 6. Synchronization Flow
Events flow from the WebSocket channel to Zustand state domains via `SynchronizationService`:
```
                WebSocket Packet
                       │
                       ▼
             SynchronizationService
                       │
             (Event Classification)
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
  ASSISTANT_STREAM  FILES_CHANGED  WORKSPACE_UPDATED
         │             │             │
         ▼             ▼             ▼
  assistantStore   filesStore     uiStore
```

---

## 7. Error Handling
* Axios error structures are normalized into `AuralisApiError` objects containing standard properties:
  - `status`: HTTP response status code (e.g., 400, 500).
  - `code`: Normalized error classification (e.g., `NETWORK_ERROR`, `HTTP_404`).
  - `message`: Server-provided exception details or default user-friendly messages.
  - `path`: Target route path causing the issue.

---

## 8. Testing Strategy
* **Client Validation**: Verifies dynamic bases, token attachments, and error mappings.
* **Auth Validation**: Asserts local memory logins and state purges.
* **WebSocket Validation**: Runs mock triggers to verify connection state machines, duplicate guards, message loops, and backoffs.
* **Sync Validation**: Simulates incoming WebSocket packages and asserts updates dispatched to Zustand store actions.

---

## 9. Backend Compatibility Assumptions
* The frontend assumes a default FastAPI host running at `http://localhost:8000`.
* Standard route expectations map to:
  - `GET /health` and `GET /status`
  - `POST /assistant` and `POST /command`
  - `GET /files/search`
  - `GET /voice/listen`
  - `POST /listener/start`, `POST /listener/stop`, `GET /listener/status`
