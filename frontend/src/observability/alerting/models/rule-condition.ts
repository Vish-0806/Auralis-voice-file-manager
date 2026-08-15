export const AlertOperator = {
  EQ: 'EQ',
  NEQ: 'NEQ',
  GT: 'GT',
  GTE: 'GTE',
  LT: 'LT',
  LTE: 'LTE',
  CONTAINS: 'CONTAINS',
  NOT_CONTAINS: 'NOT_CONTAINS',
  STARTS_WITH: 'STARTS_WITH',
  ENDS_WITH: 'ENDS_WITH',
  EXISTS: 'EXISTS',
  NOT_EXISTS: 'NOT_EXISTS',
  MATCHES: 'MATCHES'
} as const;

export type AlertOperatorValue = typeof AlertOperator[keyof typeof AlertOperator];

export interface RuleCondition {
  readonly id: string;
  readonly field: string;
  readonly operator: AlertOperatorValue;
  readonly expectedValue?: unknown;
  readonly metadata?: Record<string, unknown>;
}
