export const AlertCertificationStage = {
  FOUNDATION: 'FOUNDATION',
  RULE_VALIDATION: 'RULE_VALIDATION',
  EVALUATION: 'EVALUATION',
  GENERATION: 'GENERATION',
  FINGERPRINTING: 'FINGERPRINTING',
  DEDUPLICATION: 'DEDUPLICATION',
  LIFECYCLE: 'LIFECYCLE',
  SUPPRESSION: 'SUPPRESSION',
  NOTIFICATION: 'NOTIFICATION',
  ORCHESTRATION: 'ORCHESTRATION',
  FAILURE_ISOLATION: 'FAILURE_ISOLATION',
  CONCURRENCY: 'CONCURRENCY',
  IDEMPOTENCY: 'IDEMPOTENCY',
  IMMUTABILITY: 'IMMUTABILITY',
  BOUNDED_STORAGE: 'BOUNDED_STORAGE',
  DIAGNOSTICS: 'DIAGNOSTICS',
  STATISTICS: 'STATISTICS',
  END_TO_END: 'END_TO_END'
} as const;

export type AlertCertificationStageValue = typeof AlertCertificationStage[keyof typeof AlertCertificationStage];

export const AlertCertificationStatus = {
  CERTIFIED: 'CERTIFIED',
  CERTIFIED_WITH_WARNINGS: 'CERTIFIED_WITH_WARNINGS',
  FAILED: 'FAILED'
} as const;

export type AlertCertificationStatusValue = typeof AlertCertificationStatus[keyof typeof AlertCertificationStatus];

export interface AlertCertificationCheck {
  readonly name: string;
  readonly passed: boolean;
  readonly message?: string;
}

export interface AlertCertificationStageResult {
  readonly stage: AlertCertificationStageValue;
  readonly status: 'SUCCESS' | 'WARNING' | 'FAILED';
  readonly checks: ReadonlyArray<AlertCertificationCheck>;
  readonly durationMs: number;
}

export interface AlertCertificationReport {
  readonly status: AlertCertificationStatusValue;
  readonly score: number;
  readonly maxScore: number;
  readonly percentage: number;
  readonly stageResults: ReadonlyArray<AlertCertificationStageResult>;
  readonly passedStages: number;
  readonly failedStages: number;
  readonly warningCount: number;
  readonly certifiedAt: number;
}
