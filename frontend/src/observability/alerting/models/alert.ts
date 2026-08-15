import { AlertSeverityValue } from './severity';

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
  readonly sourceId: string;
  readonly severity: AlertSeverityValue;
  readonly state: AlertStateValue;
  readonly title: string;
  readonly message: string;
  readonly createdAt: number;
  readonly updatedAt: number;
  readonly metadata: Record<string, unknown>;

  // Extended for Phase 18.7.4
  readonly ruleId?: string;
  readonly ruleVersion?: number;
  readonly fingerprint?: string;
  readonly status?: string;
  readonly triggeredAt?: number;
  readonly generatedAt?: number;
  readonly tags?: ReadonlyArray<string>;
  readonly evaluationResult?: unknown; // RuleEvaluationResult snapshot
}