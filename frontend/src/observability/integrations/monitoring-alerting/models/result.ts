import { AlertOrchestrationResult } from '../../../alerting/models/orchestration';

export interface MonitoringAlertIntegrationResult {
  readonly occurred: boolean;
  readonly skipped: boolean;
  readonly reason?: string;
  readonly alertingResult?: AlertOrchestrationResult;
  readonly correlationId?: string;
  readonly timestamp: number;
}
