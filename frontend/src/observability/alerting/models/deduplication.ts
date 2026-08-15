export const DeduplicationScope = {
  GLOBAL: 'GLOBAL',
  PER_RULE: 'PER_RULE',
  PER_SOURCE: 'PER_SOURCE'
} as const;

export type DeduplicationScopeValue = typeof DeduplicationScope[keyof typeof DeduplicationScope];

export interface DeduplicationPolicy {
  readonly enabled: boolean;
  readonly cooldownMs: number;
  readonly scope: DeduplicationScopeValue;
  readonly maxHistorySize?: number;
}

export const DeduplicationDecisionType = {
  ACCEPTED: 'ACCEPTED',
  DUPLICATE: 'DUPLICATE',
  COOLDOWN_SUPPRESSED: 'COOLDOWN_SUPPRESSED'
} as const;

export type DeduplicationDecisionTypeValue = typeof DeduplicationDecisionType[keyof typeof DeduplicationDecisionType];

export interface DeduplicationDecision {
  readonly fingerprint: string;
  readonly alertId: string;
  readonly decision: DeduplicationDecisionTypeValue;
  readonly duplicate: boolean;
  readonly cooldownSuppressed: boolean;
  readonly firstSeenAt: number;
  readonly lastSeenAt: number;
  readonly nextEligibleAt: number;
  readonly occurrenceCount: number;
  readonly evaluatedAt: number;
  readonly reason: string;
}

export interface DeduplicationRecord {
  readonly fingerprint: string;
  readonly firstSeenAt: number;
  readonly lastSeenAt: number;
  readonly occurrenceCount: number;
  readonly acceptedCount: number;
  readonly duplicateCount: number;
  readonly cooldownSuppressionCount: number;
  readonly nextEligibleAt: number;
  readonly ruleId?: string;
  readonly sourceId?: string;
}
