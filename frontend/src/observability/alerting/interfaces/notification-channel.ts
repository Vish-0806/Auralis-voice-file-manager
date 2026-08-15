import {
  NotificationChannelTypeValue,
  NotificationRequest,
  NotificationDeliveryResult
} from '../models/notification';

export interface INotificationChannel {
  readonly id: string;
  readonly name: string;
  readonly type: NotificationChannelTypeValue;
  enabled: boolean;

  send(request: NotificationRequest): Promise<NotificationDeliveryResult>;
  validate(request: NotificationRequest): boolean;
  health(): Promise<{ status: 'HEALTHY' | 'UNHEALTHY'; message?: string }>;
  close(): Promise<void>;
}
