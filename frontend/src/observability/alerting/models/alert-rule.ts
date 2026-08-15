import { AlertSeverityValue } from './severity';
import { ConditionGroup } from './condition-group';

export interface AlertRule {
  readonly id: string;
  readonly name: string;
  readonly description: string;
  readonly enabled: boolean;
  readonly severity: AlertSeverityValue;
  readonly conditions: ConditionGroup;
  readonly sourceId: string;
  readonly tags: ReadonlyArray<string>;
  readonly createdAt: number;
  readonly updatedAt: number;
  readonly version?: number;
  readonly metadata: Record<string, unknown>;
}
