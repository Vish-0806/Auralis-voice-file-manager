import { RuleEvaluationResult, AlertEvaluationContext } from './evaluation';
import { AlertRecord } from './alert';
import { DeduplicationDecision } from './deduplication';
import { AlertSuppressionDecision } from './suppression';
import { AlertLifecycleRecord } from './lifecycle';
import { NotificationDeliveryResult, NotificationPriorityValue, NotificationChannelTypeValue, NotificationRecipient } from './notification';

export const AlertOrchestrationStage = {
  EVALUATION: 'EVALUATION',
  GENERATION: 'GENERATION',
  DEDUPLICATION: 'DEDUPLICATION',
  SUPPRESSION: 'SUPPRESSION',
  LIFECYCLE: 'LIFECYCLE',
  NOTIFICATION: 'NOTIFICATION',
  COMPLETED: 'COMPLETED'
} as const;

export type AlertOrchestrationStageValue = typeof AlertOrchestrationStage[keyof typeof AlertOrchestrationStage];

export const AlertOrchestrationStatus = {
  PENDING: 'PENDING',
  RUNNING: 'RUNNING',
  SUCCESS: 'SUCCESS',
  SKIPPED: 'SKIPPED',
  FAILED: 'FAILED',
  SUPPRESSED: 'SUPPRESSED',
  DUPLICATE: 'DUPLICATE',
  COMPLETED: 'COMPLETED'
} as const;

export type AlertOrchestrationStatusValue = typeof AlertOrchestrationStatus[keyof typeof AlertOrchestrationStatus];

export interface AlertOrchestrationStageResult {
  readonly stage: AlertOrchestrationStageValue;
  readonly status: AlertOrchestrationStatusValue;
  readonly timestamp: number;
  readonly duration: number;
  readonly error?: { name: string; message: string; stack?: string };
}

export interface AlertOrchestrationRequest {
  readonly orchestrationId: string;
  readonly ruleId: string;
  readonly context: AlertEvaluationContext;
  readonly channelId?: string;
  readonly recipient?: NotificationRecipient;
  readonly priority?: NotificationPriorityValue;
  readonly channelType?: NotificationChannelTypeValue;
  readonly correlationId?: string;
}

export interface AlertOrchestrationResult {
  readonly orchestrationId: string;
  readonly alertId?: string;
  readonly ruleId: string;
  readonly fingerprint?: string;
  readonly status: AlertOrchestrationStatusValue;
  readonly stageResults: ReadonlyArray<AlertOrchestrationStageResult>;
  readonly evaluationResult?: RuleEvaluationResult;
  readonly generationResult?: AlertRecord;
  readonly deduplicationDecision?: DeduplicationDecision;
  readonly suppressionDecision?: AlertSuppressionDecision;
  readonly lifecycleResult?: AlertLifecycleRecord;
  readonly notificationResult?: NotificationDeliveryResult;
  readonly attemptedAt: number;
  readonly completedAt: number;
  readonly duration: number;
}
