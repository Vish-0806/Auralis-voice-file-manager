export const AlertSeverity = {
  INFO: 'INFO',
  WARNING: 'WARNING',
  ERROR: 'ERROR',
  CRITICAL: 'CRITICAL'
} as const;

export type AlertSeverityValue = typeof AlertSeverity[keyof typeof AlertSeverity];

export const AlertState = {
  ACTIVE: 'ACTIVE',
  ACKNOWLEDGED: 'ACKNOWLEDGED',
  SUPPRESSED: 'SUPPRESSED',
  RESOLVED: 'RESOLVED',
  EXPIRED: 'EXPIRED'
} as const;

export type AlertStateValue = typeof AlertState[keyof typeof AlertState];

export interface AlertRecord {
  readonly id: string;
  readonly ruleId: string;
  readonly sourceId: string;
  readonly fingerprint: string;
  readonly severity: AlertSeverityValue;
  readonly state: AlertStateValue;
  readonly title: string;
  readonly message: string;
  readonly createdAt: number;
  readonly updatedAt: number;
  readonly acknowledgedAt?: number | null;
  readonly acknowledgedBy?: string | null;
  readonly resolvedAt?: number | null;
  readonly resolvedBy?: string | null;
  readonly suppressedUntil?: number | null;
  readonly expiresAt?: number | null;
  readonly metadata: Record<string, unknown>;
}

export const AlertingRuntimeState = {
  UNINITIALIZED: 'UNINITIALIZED',
  INITIALIZING: 'INITIALIZING',
  READY: 'READY',
  EVALUATING: 'EVALUATING',
  STOPPING: 'STOPPING',
  STOPPED: 'STOPPED',
  ERROR: 'ERROR'
} as const;

export type AlertingRuntimeStateValue = typeof AlertingRuntimeState[keyof typeof AlertingRuntimeState];

