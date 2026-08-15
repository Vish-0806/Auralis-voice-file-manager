import { INotificationChannel } from '../interfaces/notification-channel';
import {
  NotificationChannelTypeValue,
  NotificationRequest,
  NotificationDeliveryResult
} from '../models/notification';
import { createNotificationDeliveryResult, createNotificationDeliveryAttempt } from '../factories/alertingFactories';

export class InMemoryNotificationChannel implements INotificationChannel {
  public readonly id: string;
  public readonly name: string;
  public readonly type: NotificationChannelTypeValue;
  public enabled = true;

  private readonly _sentRequests: NotificationRequest[] = [];
  private _simulateFailuresRemaining = 0;
  private _simulateUnhealthy = false;

  constructor(id: string, name: string, type: NotificationChannelTypeValue = 'CUSTOM') {
    this.id = id;
    this.name = name;
    this.type = type;
  }

  public async send(request: NotificationRequest): Promise<NotificationDeliveryResult> {
    const start = Date.now();
    this._sentRequests.push(request);

    if (this._simulateFailuresRemaining > 0) {
      this._simulateFailuresRemaining--;
      const duration = Date.now() - start;
      const attempt = createNotificationDeliveryAttempt({
        notificationId: request.id,
        attempt: 1,
        status: 'FAILED',
        timestamp: start,
        duration,
        error: { name: 'SimulatedFailure', message: 'Simulated failure in test channel' }
      });

      return createNotificationDeliveryResult({
        notificationId: request.id,
        channelId: this.id,
        status: 'FAILED',
        error: { name: 'SimulatedFailure', message: 'Simulated failure in test channel' },
        attemptedAt: start,
        completedAt: Date.now(),
        duration,
        attempts: 1,
        history: [attempt]
      });
    }

    const duration = Date.now() - start;
    const attempt = createNotificationDeliveryAttempt({
      notificationId: request.id,
      attempt: 1,
      status: 'DELIVERED',
      timestamp: start,
      duration
    });

    return createNotificationDeliveryResult({
      notificationId: request.id,
      channelId: this.id,
      status: 'DELIVERED',
      attemptedAt: start,
      completedAt: Date.now(),
      duration,
      attempts: 1,
      history: [attempt]
    });
  }

  public validate(request: NotificationRequest): boolean {
    if (!request.id || !request.alertId || !request.payload.title || !request.payload.message) {
      return false;
    }
    return true;
  }

  public async health(): Promise<{ status: 'HEALTHY' | 'UNHEALTHY'; message?: string }> {
    if (this._simulateUnhealthy) {
      return { status: 'UNHEALTHY', message: 'Simulated unhealthy state' };
    }
    return { status: 'HEALTHY' };
  }

  public async close(): Promise<void> {
    this._sentRequests.length = 0;
  }

  // Test helpers
  public simulateFailures(count: number): void {
    this._simulateFailuresRemaining = count;
  }

  public simulateUnhealthy(unhealthy: boolean): void {
    this._simulateUnhealthy = unhealthy;
  }

  public getSentRequests(): ReadonlyArray<NotificationRequest> {
    return this._sentRequests;
  }

  public clearSentRequests(): void {
    this._sentRequests.length = 0;
  }
}
