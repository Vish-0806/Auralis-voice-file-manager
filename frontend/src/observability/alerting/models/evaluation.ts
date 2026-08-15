export interface AlertEvaluationContext {
  readonly values: Record<string, unknown>;
}

export const ConditionEvaluationStatus = {
  MATCHED: 'MATCHED',
  NOT_MATCHED: 'NOT_MATCHED',
  ERROR: 'ERROR',
  SKIPPED: 'SKIPPED'
} as const;

export type ConditionEvaluationStatusValue = typeof ConditionEvaluationStatus[keyof typeof ConditionEvaluationStatus];

export interface ConditionEvaluationResult {
  readonly conditionId: string;
  readonly matched: boolean;
  readonly status: ConditionEvaluationStatusValue;
  readonly actualValue: unknown;
  readonly expectedValue: unknown;
  readonly operator: string;
  readonly field: string;
  readonly reason?: string;
  readonly error?: {
    readonly name: string;
    readonly message: string;
    readonly stack?: string;
  };
  readonly durationMs?: number;
}

export interface GroupEvaluationResult {
  readonly operator: 'ALL' | 'ANY' | 'NOT';
  readonly matched: boolean;
  readonly conditions: ReadonlyArray<ConditionEvaluationResult | GroupEvaluationResult>;
  readonly reason?: string;
  readonly durationMs?: number;
}

export const RuleEvaluationStatus = {
  MATCHED: 'MATCHED',
  NOT_MATCHED: 'NOT_MATCHED',
  ERROR: 'ERROR',
  SKIPPED: 'SKIPPED'
} as const;

export type RuleEvaluationStatusValue = typeof RuleEvaluationStatus[keyof typeof RuleEvaluationStatus];

export interface RuleEvaluationResult {
  readonly ruleId: string;
  readonly ruleVersion?: number;
  readonly matched: boolean;
  readonly status: RuleEvaluationStatusValue;
  readonly results: GroupEvaluationResult;
  readonly evaluatedAt: number;
  readonly durationMs: number;
  readonly error?: {
    readonly name: string;
    readonly message: string;
    readonly stack?: string;
  };
  readonly metadata: Record<string, unknown>;
}
