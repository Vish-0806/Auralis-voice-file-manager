export const AlertingRuntimeState = {
  UNINITIALIZED: 'UNINITIALIZED',
  INITIALIZING: 'INITIALIZING',
  READY: 'READY',
  STOPPING: 'STOPPING',
  STOPPED: 'STOPPED',
  ERROR: 'ERROR'
} as const;

export type AlertingRuntimeStateValue = typeof AlertingRuntimeState[keyof typeof AlertingRuntimeState];