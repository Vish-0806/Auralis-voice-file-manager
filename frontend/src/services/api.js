/**
 * API service for communicating with the Auralis backend.
 * Integrates with endpoints defined in backend routes.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Sends a text command to be parsed and executed.
 * @param {string} command - The text command to execute (e.g., "create folder Projects")
 * @returns {Promise<object>} Structured result from the backend
 */
export async function sendCommand(command) {
  const response = await fetch(`${API_BASE}/command`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ command }),
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Command execution failed: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Triggers microphone listening on the backend.
 * @returns {Promise<object>} Result containing recognized text, parsed action, and execution outcome
 */
export async function triggerVoiceListen() {
  const response = await fetch(`${API_BASE}/voice/listen`);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Voice listening failed. Please try again.');
  }
  
  return response.json();
}

/**
 * Starts the continuous listener in a background thread on the backend.
 * @returns {Promise<object>} Status response
 */
export async function startListener() {
  const response = await fetch(`${API_BASE}/listener/start`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to start continuous listener.');
  }
  
  return response.json();
}

/**
 * Stops the continuous listener on the backend.
 * @returns {Promise<object>} Status response
 */
export async function stopListener() {
  const response = await fetch(`${API_BASE}/listener/stop`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to stop continuous listener.');
  }
  
  return response.json();
}

/**
 * Fetches the current running status of the continuous listener.
 * @returns {Promise<object>} e.g., { running: boolean, status: "running" | "stopped" }
 */
export async function getListenerStatus() {
  const response = await fetch(`${API_BASE}/listener/status`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch listener status.');
  }
  
  return response.json();
}

/**
 * Recursively searches for files matching a query.
 * @param {string} query - Filename query to search for
 * @returns {Promise<Array>} List of matched file objects { name, path, type }
 */
export async function searchFiles(query) {
  const response = await fetch(`${API_BASE}/files/search?query=${encodeURIComponent(query)}`);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to search files.');
  }
  
  return response.json();
}
