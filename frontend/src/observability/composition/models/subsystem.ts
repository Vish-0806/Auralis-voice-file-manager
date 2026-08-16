export const ObservabilitySubsystem = {
  MONITORING: 'MONITORING',
  LOGGING: 'LOGGING',
  METRICS: 'METRICS',
  TRACING: 'TRACING',
  TELEMETRY: 'TELEMETRY',
  DIAGNOSTICS: 'DIAGNOSTICS',
  ALERTING: 'ALERTING'
} as const;

export type ObservabilitySubsystemValue = typeof ObservabilitySubsystem[keyof typeof ObservabilitySubsystem];

export interface ObservabilitySubsystemState {
  readonly subsystem: ObservabilitySubsystemValue;
  readonly state: string;
  readonly healthy: boolean;
}
