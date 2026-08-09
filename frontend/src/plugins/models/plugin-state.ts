export const PluginState = {
  UNREGISTERED: 'UNREGISTERED',
  REGISTERED: 'REGISTERED',
  INITIALIZING: 'INITIALIZING',
  READY: 'READY',
  DISABLED: 'DISABLED',
  ERROR: 'ERROR',
  DISPOSED: 'DISPOSED',
} as const;

export type PluginStateValue = (typeof PluginState)[keyof typeof PluginState];
