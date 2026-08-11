export const AlertOperator = {
  EQUALS: 'EQUALS',
  NOT_EQUALS: 'NOT_EQUALS',
  GREATER_THAN: 'GREATER_THAN',
  GREATER_THAN_OR_EQUAL: 'GREATER_THAN_OR_EQUAL',
  LESS_THAN: 'LESS_THAN',
  LESS_THAN_OR_EQUAL: 'LESS_THAN_OR_EQUAL',
  EXISTS: 'EXISTS',
  NOT_EXISTS: 'NOT_EXISTS'
} as const;

export type AlertOperatorValue = typeof AlertOperator[keyof typeof AlertOperator];

export interface AlertCondition {
  readonly field: string;
  readonly operator: AlertOperatorValue;
  readonly expectedValue?: unknown;
  readonly threshold?: number;
  readonly metadata?: Record<string, unknown>;
}

export interface AlertConditionGroup {
  readonly operator: 'ALL' | 'ANY';
  readonly conditions: ReadonlyArray<AlertCondition | AlertConditionGroup>;
}
