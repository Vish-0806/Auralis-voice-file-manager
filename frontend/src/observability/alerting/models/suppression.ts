export const AlertSuppressionReason = {
  MAINTENANCE: 'MAINTENANCE',
  POLICY: 'POLICY',
  SNOOZED: 'SNOOZED',
  MANUAL: 'MANUAL',
  RATE_LIMITED: 'RATE_LIMITED',
  DISABLED: 'DISABLED'
} as const;

export type AlertSuppressionReasonValue = typeof AlertSuppressionReason[keyof typeof AlertSuppressionReason];

export const AlertSuppressionScope = {
  ALERT: 'ALERT',
  FINGERPRINT: 'FINGERPRINT',
  RULE: 'RULE',
  SOURCE: 'SOURCE',
  GLOBAL: 'GLOBAL'
} as const;

export type AlertSuppressionScopeValue = typeof AlertSuppressionScope[keyof typeof AlertSuppressionScope];

export interface AlertSuppressionPolicy {
  readonly id: string;
  readonly name: string;
  readonly enabled: boolean;
  readonly priority: number;
  readonly scope: AlertSuppressionScopeValue;
  readonly ruleId?: string;
  readonly alertId?: string;
  readonly fingerprint?: string;
  readonly sourceId?: string;
  readonly startTime?: number;
  readonly endTime?: number;
  readonly reason: AlertSuppressionReasonValue;
  readonly metadata?: Record<string, unknown>;
}

export interface AlertMaintenanceWindow {
  readonly id: string;
  readonly name: string;
  readonly enabled: boolean;
  readonly startTime: number;
  readonly endTime: number;
  readonly scope?: AlertSuppressionScopeValue;
  readonly reason: string;
  readonly metadata?: Record<string, unknown>;
}

export interface AlertSnoozeRecord {
  readonly alertId: string;
  readonly fingerprint?: string;
  readonly startTime: number;
  readonly endTime: number;
  readonly actor: string;
  readonly reason?: string;
  readonly metadata?: Record<string, unknown>;
}

export interface AlertSuppressionDecision {
  readonly suppressed: boolean;
  readonly reason: AlertSuppressionReasonValue | null;
  readonly policyId?: string;
  readonly windowId?: string;
  readonly evaluatedAt: number;
  readonly metadata?: Record<string, unknown>;
}
