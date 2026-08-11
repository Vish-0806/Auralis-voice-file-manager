import { AlertSeverityValue } from './alert';
import { AlertCondition, AlertConditionGroup } from './condition';

export interface AlertRule {
  readonly id: string;
  readonly name: string;
  readonly description: string;
  readonly enabled: boolean;
  readonly severity: AlertSeverityValue;
  readonly sourceId: string;
  readonly priority: number;
  readonly cooldownMs?: number;
  readonly suppressionMs?: number;
  readonly expirationMs?: number;
  readonly conditions: AlertConditionGroup | ReadonlyArray<AlertCondition>;
  readonly metadata: Record<string, unknown>;
}
