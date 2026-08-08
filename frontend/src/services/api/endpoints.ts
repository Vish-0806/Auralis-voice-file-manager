export const ENDPOINTS = {
  HEALTH: '/health',
  STATUS: '/status',
  ASSISTANT: '/assistant',
  COMMAND: '/command',
  FILES: {
    SEARCH: '/files/search',
  },
  VOICE: {
    LISTEN: '/voice/listen',
  },
  LISTENER: {
    START: '/listener/start',
    STOP: '/listener/stop',
    STATUS: '/listener/status',
  }
} as const;
