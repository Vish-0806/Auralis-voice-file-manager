import { AlertEvaluationContext } from '../../../alerting/models/evaluation';

export interface MonitoringAlertRequest {
  readonly orchestrationId: string;
  readonly ruleId: string;
  readonly context: AlertEvaluationContext;
  readonly correlationId?: string;
  readonly metadata?: Record<string, unknown>;
}
