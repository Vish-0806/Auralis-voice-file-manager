export const NotificationChannelType = {
  IN_APP: 'IN_APP',
  EMAIL: 'EMAIL',
  PUSH: 'PUSH',
  WEBHOOK: 'WEBHOOK',
  CUSTOM: 'CUSTOM'
} as const;

export type NotificationChannelTypeValue = typeof NotificationChannelType[keyof typeof NotificationChannelType];

export const NotificationChannelStatus = {
  ENABLED: 'ENABLED',
  DISABLED: 'DISABLED'
} as const;

export type NotificationChannelStatusValue = typeof NotificationChannelStatus[keyof typeof NotificationChannelStatus];

export const NotificationPriority = {
  LOW: 'LOW',
  NORMAL: 'NORMAL',
  HIGH: 'HIGH',
  CRITICAL: 'CRITICAL'
} as const;

export type NotificationPriorityValue = typeof NotificationPriority[keyof typeof NotificationPriority];

export const NotificationDeliveryStatus = {
  QUEUED: 'QUEUED',
  SENDING: 'SENDING',
  DELIVERED: 'DELIVERED',
  FAILED: 'FAILED',
  SKIPPED: 'SKIPPED',
  CANCELLED: 'CANCELLED'
} as const;

export type NotificationDeliveryStatusValue = typeof NotificationDeliveryStatus[keyof typeof NotificationDeliveryStatus];

export interface NotificationRecipient {
  readonly id: string;
  readonly name: string;
  readonly address?: string;
}

export interface NotificationPayload {
  readonly title: string;
  readonly message: string;
  readonly severity: string;
  readonly metadata?: Record<string, unknown>;
}

export interface NotificationRequest {
  readonly id: string;
  readonly alertId: string;
  readonly fingerprint?: string;
  readonly channelId: string;
  readonly payload: NotificationPayload;
  readonly priority: NotificationPriorityValue;
  readonly channelType: NotificationChannelTypeValue;
  readonly recipient: NotificationRecipient;
  readonly createdAt: number;
  readonly correlationId?: string;
}

export interface NotificationDeliveryAttempt {
  readonly notificationId: string;
  readonly attempt: number;
  readonly status: NotificationDeliveryStatusValue;
  readonly timestamp: number;
  readonly duration: number;
  readonly error?: { name: string; message: string; stack?: string };
}

export interface NotificationDeliveryResult {
  readonly notificationId: string;
  readonly channelId: string;
  readonly status: NotificationDeliveryStatusValue;
  readonly error?: { name: string; message: string; stack?: string };
  readonly attemptedAt: number;
  readonly completedAt: number;
  readonly duration: number;
  readonly attempts: number;
  readonly history: ReadonlyArray<NotificationDeliveryAttempt>;
}
