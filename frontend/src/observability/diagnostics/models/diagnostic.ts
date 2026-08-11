export const DiagnosticSeverity = {
  INFO: 'INFO',
  WARNING: 'WARNING',
  ERROR: 'ERROR',
  CRITICAL: 'CRITICAL'
} as const;

export type DiagnosticSeverityValue = typeof DiagnosticSeverity[keyof typeof DiagnosticSeverity];

export const DiagnosticStatus = {
  HEALTHY: 'HEALTHY',
  DEGRADED: 'DEGRADED',
  UNHEALTHY: 'UNHEALTHY',
  UNKNOWN: 'UNKNOWN',
  DISABLED: 'DISABLED'
} as const;

export type DiagnosticStatusValue = typeof DiagnosticStatus[keyof typeof DiagnosticStatus];

export const DiagnosticCategory = {
  RUNTIME: 'RUNTIME',
  PERFORMANCE: 'PERFORMANCE',
  AVAILABILITY: 'AVAILABILITY',
  SECURITY: 'SECURITY',
  CONFIGURATION: 'CONFIGURATION',
  DEPENDENCY: 'DEPENDENCY',
  RESOURCE: 'RESOURCE',
  INTEGRATION: 'INTEGRATION',
  CUSTOM: 'CUSTOM'
} as const;

export type DiagnosticCategoryValue = typeof DiagnosticCategory[keyof typeof DiagnosticCategory];

export interface DiagnosticRecord {
  readonly id: string;
  readonly sourceId: string;
  readonly componentId: string;
  readonly category: DiagnosticCategoryValue;
  readonly severity: DiagnosticSeverityValue;
  readonly status: DiagnosticStatusValue;
  readonly title: string;
  readonly message: string;
  readonly timestamp: number;
  readonly duration: number;
  readonly metadata: Record<string, unknown>;
  readonly relatedIdentifiers?: ReadonlyArray<string>;
}

export const DiagnosticsRuntimeState = {
  UNINITIALIZED: 'UNINITIALIZED',
  INITIALIZING: 'INITIALIZING',
  READY: 'READY',
  RUNNING: 'RUNNING',
  STOPPING: 'STOPPING',
  STOPPED: 'STOPPED',
  ERROR: 'ERROR'
} as const;

export type DiagnosticsRuntimeStateValue = typeof DiagnosticsRuntimeState[keyof typeof DiagnosticsRuntimeState];

