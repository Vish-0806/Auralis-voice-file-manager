export const MonitoringRuntimeState = {
  UNINITIALIZED: 'UNINITIALIZED',
  INITIALIZING: 'INITIALIZING',
  READY: 'READY',
  STOPPING: 'STOPPING',
  STOPPED: 'STOPPED',
  ERROR: 'ERROR'
} as const;

export type MonitoringRuntimeStateValue = typeof MonitoringRuntimeState[keyof typeof MonitoringRuntimeState];
