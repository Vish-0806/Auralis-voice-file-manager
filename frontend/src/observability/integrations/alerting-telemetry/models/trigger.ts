import { AlertSeverityValue } from '../../../alerting/models/severity';
import { AlertLifecycleStateValue } from '../../../alerting/models/lifecycle';

export type AlertingTelemetryTriggerKind =
  | 'EVALUATED'
  | 'GENERATED'
  | 'DEDUPLICATED'
  | 'SUPPRESSED'
  | 'LIFECYCLE_CHANGED'
  | 'NOTIFICATION_DISPATCHED'
  | 'ORCHESTRATION_COMPLETED'
  | 'ORCHESTRATION_FAILED';

export interface AlertingTelemetryTrigger {
  readonly triggerId: string;
  readonly kind: AlertingTelemetryTriggerKind;
  readonly timestamp: number;
  readonly alertId?: string;
  readonly fingerprint?: string;
  readonly ruleId?: string;
  readonly sourceId?: string;
  readonly correlationId?: string;
  readonly traceId?: string;
  readonly requestId?: string;
  readonly operationId?: string;
  readonly lifecycleState?: AlertLifecycleStateValue;
  readonly severity?: AlertSeverityValue;
  readonly status?: string;
  readonly orchestrationStatus?: string;
  readonly notificationStatus?: string;
  readonly metadata?: Record<string, unknown>;
  readonly payload?: any;
}
