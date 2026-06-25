# API Reference

This reference lists all available REST API endpoints for Auralis. All endpoints route their logic strictly through the unified `AuralisAssistant` orchestrator facade.

---

## 1. General Command Routing

### Handle Command
- **Endpoint:** `POST /command`
- **Description:** Sends a raw text command to the assistant for reasoning and execution.
- **Request Body:**
  ```json
  {
    "command": "delete report.pdf"
  }
  ```
- **Response Example:**
  ```json
  {
    "status": "success",
    "command": "delete report.pdf",
    "parsed_action": {
      "action": "delete",
      "target": "report.pdf"
    },
    "result": {
      "status": "pending_confirmation",
      "message": "Are you sure you want to delete report.pdf?"
    }
  }
  ```

---

## 2. File Operations

### Search Files
- **Endpoint:** `GET /files/search`
- **Description:** Recursively search Desktop, Documents, and Downloads directories for filenames matching a term.
- **Query Parameters:**
  - `query` (string, required): Search query/pattern.
- **Response Example:**
  ```json
  [
    {
      "name": "report.pdf",
      "path": "C:\\Users\\User\\Desktop\\report.pdf",
      "type": ".pdf"
    }
  ]
  ```

---

## 3. Voice & Listener Management

### Start Continuous Listener
- **Endpoint:** `POST /listener/start`
- **Description:** Starts the background continuous voice listening thread.
- **Response Example:**
  ```json
  {
    "status": "started",
    "message": "Listener started successfully"
  }
  ```

### Stop Continuous Listener
- **Endpoint:** `POST /listener/stop`
- **Description:** Stops the background continuous voice listening thread.
- **Response Example:**
  ```json
  {
    "status": "stopped",
    "message": "Listener stopped successfully"
  }
  ```

### Get Listener Status
- **Endpoint:** `GET /listener/status`
- **Description:** Returns whether the continuous background listener is currently running.
- **Response Example:**
  ```json
  {
    "running": true,
    "status": "running"
  }
  ```

### Listen Voice Command
- **Endpoint:** `GET /voice/listen`
- **Description:** Actively listens to the microphone once, converts speech to text, validates the wake word, parses the command, classifies intent if an action is pending, executes the action, formats a response, and outputs spoken feedback using TTS.
- **Response Example (Ignored without Wake Word):**
  ```json
  {
    "status": "ignored",
    "message": "Wake word not detected"
  }
  ```
- **Response Example (Success):**
  ```json
  {
    "status": "success",
    "recognized_text": "hey auralis search report",
    "command": "search report",
    "parsed_action": {
      "action": "search",
      "target": "report"
    },
    "result": [
      {
        "name": "report.pdf",
        "path": "C:\\Users\\User\\Desktop\\report.pdf",
        "type": ".pdf"
      }
    ]
  }
  ```
