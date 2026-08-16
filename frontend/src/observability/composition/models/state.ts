export const ObservabilityCompositionState = {
  UNINITIALIZED: 'UNINITIALIZED',
  INITIALIZING: 'INITIALIZING',
  READY: 'READY',
  STOPPING: 'STOPPING',
  STOPPED: 'STOPPED',
  FAILED: 'FAILED'
} as const;

export type ObservabilityCompositionStateValue = typeof ObservabilityCompositionState[keyof typeof ObservabilityCompositionState];
