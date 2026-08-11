export interface AlertConditionResult {
  readonly field: string;
  readonly matched: boolean;
  readonly actualValue?: unknown;
  readonly expectedValue?: unknown;
  readonly operator: string;
}

export interface AlertEvaluationResult {
  readonly ruleId: string;
  readonly matched: boolean;
  readonly evaluatedAt: number;
  readonly duration: number;
  readonly conditionResults: ReadonlyArray<AlertConditionResult>;
  readonly reason?: string | null;
  readonly error?: {
    readonly name: string;
    readonly message: string;
    readonly stack?: string;
  } | null;
  readonly metadata: Record<string, unknown>;
}
