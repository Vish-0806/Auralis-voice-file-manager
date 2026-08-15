import { RuleCondition } from './rule-condition';

export interface ConditionGroup {
  readonly operator: 'ALL' | 'ANY' | 'NOT';
  readonly conditions: ReadonlyArray<RuleCondition | ConditionGroup>;
}
